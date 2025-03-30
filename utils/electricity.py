from datetime import datetime
from typing import Optional, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression

from ..csust_api import ElectricityInfo, csust_api
from ..db.electricity_db import ElectricityHistory, SessionLocal


def update_electricity_history(
    electricity_info: ElectricityInfo,
    campus: str,
    building: str,
    room: str,
) -> bool:
    with SessionLocal() as session:
        last_record = (
            session.query(ElectricityHistory)
            .filter(
                ElectricityHistory.campus == campus,
                ElectricityHistory.building == building,
                ElectricityHistory.room == room,
            )
            .order_by(ElectricityHistory.record_time.desc())
            .first()
        )
        if not last_record or last_record.electricity != electricity_info.value:
            session.add(
                ElectricityHistory(
                    electricity=electricity_info.value,
                    campus=campus,
                    building=building,
                    room=room,
                )
            )
            session.commit()
            return True
        return False


def predict_empty_time(campus: str, building: str, room: str) -> Optional[datetime]:
    with SessionLocal() as session:
        records = (
            session.query(ElectricityHistory)
            .filter(
                ElectricityHistory.campus == campus,
                ElectricityHistory.building == building,
                ElectricityHistory.room == room,
            )
            .order_by(ElectricityHistory.record_time.desc())
            .all()
        )

        if len(records) < 2:
            return None

        # 转换成降序时间顺序的记录
        records.reverse()

        # 找出最后一段连续下降的记录
        current_segment = []
        for i in range(len(records)):
            if i == 0 or records[i].electricity <= records[i - 1].electricity:
                current_segment.append((records[i].record_time, records[i].electricity))
            else:
                # 电量增加了，说明充值了，重新开始记录
                current_segment = [(records[i].record_time, records[i].electricity)]

        # 如果最后一段只有一个点，无法预测
        if len(current_segment) < 2:
            return None

        # 使用线性回归预测
        times = np.array([t[0].timestamp() for t in current_segment]).reshape(-1, 1)
        values = np.array([v[1] for v in current_segment]).reshape(-1, 1)

        model = LinearRegression()
        model.fit(times, values)

        m = model.coef_[0][0]
        b = model.intercept_[0]

        # 如果斜率为正或为零，则电量在增加，不需要预测
        if m >= 0:
            return None

        # 计算电量为0时的时间点
        empty_time_timestamp = -b / m
        empty_time = datetime.fromtimestamp(empty_time_timestamp)

        return empty_time


def query_electricity(
    campus: str, building: str, room: str
) -> Tuple[ElectricityInfo, Optional[datetime]]:
    electricity_info = csust_api.get_electricity(campus, building, room)
    update_electricity_history(electricity_info, campus, building, room)
    empty_time = predict_empty_time(campus, building, room)
    return electricity_info, empty_time


def validate_time_format(time_str: str) -> bool:
    try:
        hour, minute = time_str.split(":")
        hour_int, minute_int = int(hour), int(minute)
        return 0 <= hour_int < 24 and 0 <= minute_int < 60
    except (ValueError, TypeError):
        return False
