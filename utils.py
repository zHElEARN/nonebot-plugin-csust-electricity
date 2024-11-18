import time
from .data_manager import data_manager
from .csust_api import fetch_electricity_data, building_data

import numpy
from datetime import datetime
from sklearn.linear_model import LinearRegression


def estimate_discharging_time(electricity_records):
    if len(electricity_records) < 2:
        return None

    # 提取时间戳和电量值
    timestamps = [
        datetime.fromisoformat(record[0]).timestamp()
        for record in electricity_records
    ]
    electricity_values = [
        record[1] for record in electricity_records
    ]

    # 找到最近一次电量增加（充值）的索引
    last_recharge_index = 0
    for i in range(1, len(electricity_values)):
        if electricity_values[i] > electricity_values[i - 1]:
            last_recharge_index = i

    # 使用最近一次充值后的数据进行估计
    x = numpy.array(timestamps[last_recharge_index:]).reshape(-1, 1)
    y = numpy.array(electricity_values[last_recharge_index:]).reshape(-1, 1)

    if len(x) < 2:
        return None

    # 进行线性回归
    model = LinearRegression().fit(x, y)

    # 确保电量在下降，否则无法估计
    if model.coef_[0][0] >= 0:
        return None

    # 计算电量耗尽的时间
    predicted_time_seconds = (model.intercept_ / -model.coef_)[0][0]
    predicted_datetime = datetime.fromtimestamp(predicted_time_seconds)
    return predicted_datetime


def store_electricity_data(campus, building_name, room_id, remaining_power):
    data_manager.load_electricity_data()
    room_key = f"{campus}-{building_name}-{room_id}"
    timestamp = datetime.now().isoformat()
    new_entry = [timestamp, remaining_power]

    if (
        room_key not in data_manager.electricity_data
        or data_manager.electricity_data[room_key][-1][1] != remaining_power
    ):
        if room_key not in data_manager.electricity_data:
            data_manager.electricity_data[room_key] = []
        data_manager.electricity_data[room_key].append(new_entry)
        data_manager.save_electricity_data()

    if len(data_manager.electricity_data[room_key]) >= 2:
        estimated_time = estimate_discharging_time(
            data_manager.electricity_data[room_key]
        )
        if estimated_time:
            return estimated_time


async def query_electricity(
    campus, building_name, room_id, handler, prefix, id
):
    if campus not in building_data or building_name not in building_data[campus]:
        await handler.finish("校区或宿舍楼名称错误，请检查输入")

    building_id = building_data[campus][building_name]
    remaining_power = fetch_electricity_data(campus, building_id, room_id)

    if remaining_power != "未知":
        update_query_limit(prefix, id)  # 更新查询记录

        # 保存电量数据
        estimated_time = store_electricity_data(
            campus, building_name, room_id, remaining_power
        )

        msg = f"{campus}校区 {building_name} {room_id} 的剩余电量为：{remaining_power}度"
        if estimated_time:
            estimated_time_str = estimated_time.strftime("%Y-%m-%d %H:%M:%S")
            msg += f"\n预计电量耗尽时间：{estimated_time_str}"
        await handler.finish(msg)
    else:
        await handler.finish("未能获取电量信息，请检查宿舍号是否正确")


def check_query_limit(prefix, id):
    current_time = time.time()
    if id in data_manager.query_limit_data[prefix]:
        last_time, count = data_manager.query_limit_data[prefix][id]
        # 若在一小时内查询次数达到两次
        if current_time - last_time < 3600 and count >= 2:
            return False
        # 若超过一小时，则重置查询次数
        elif current_time - last_time >= 3600:
            data_manager.query_limit_data[prefix][id] = (current_time, 0)
            data_manager.save_query_limit_data()
            return True
    else:
        data_manager.query_limit_data[prefix][id] = (current_time, 0)
        data_manager.save_query_limit_data()
    return True


def update_query_limit(prefix, id):
    current_time = time.time()
    if id in data_manager.query_limit_data[prefix]:
        last_time, count = data_manager.query_limit_data[prefix][id]
        if current_time - last_time < 3600:
            data_manager.query_limit_data[prefix][id] = (last_time, count + 1)
        else:
            data_manager.query_limit_data[prefix][id] = (current_time, 1)
    else:
        data_manager.query_limit_data[prefix][id] = (current_time, 1)
    data_manager.save_query_limit_data()
