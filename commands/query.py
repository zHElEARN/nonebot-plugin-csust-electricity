from datetime import datetime

import numpy as np
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Event,
    GroupMessageEvent,
    Message,
    PrivateMessageEvent,
)
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from nonebot.rule import to_me
from sklearn.linear_model import LinearRegression

from ..csust_api import ElectricityInfo, csust_api
from ..db.electricity_db import Binding, ElectricityHistory, SessionLocal

query_command = on_command("电量", rule=to_me())


def predict_empty_time(campus: str, building: str, room: str):
    """预测电量耗尽的时间"""
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
            if i == 0 or records[i].electricity <= records[i-1].electricity:
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


@query_command.handle()
async def handle_query(event: Event, args: Message = CommandArg()):
    try:
        if isinstance(event, PrivateMessageEvent):
            sender_type = "user"
            id = str(event.get_user_id())
        elif isinstance(event, GroupMessageEvent):
            sender_type = "group"
            id = str(event.group_id)
        else:
            await query_command.finish("不支持的信息类型")
            return
        args_text = args.extract_plain_text().strip()
        if not args_text:
            # 绑定宿舍查询
            with SessionLocal() as session:
                if sender_type == "user":
                    binding = (
                        session.query(Binding).filter(Binding.qq_number == id).first()
                    )
                else:
                    binding = (
                        session.query(Binding)
                        .filter(Binding.group_number == id)
                        .first()
                    )
            if not binding:
                await query_command.finish(
                    "您还没有绑定宿舍，请先使用命令绑定宿舍\n"
                    "格式：/绑定 [校区] [楼栋] [房间号]"
                )
                return
            electricity_info = csust_api.get_electricity(
                binding.campus, binding.building, binding.room
            )
            update_electricity_history(
                electricity_info, binding.campus, binding.building, binding.room
            )
            
            # 预测电量耗尽时间
            empty_time = predict_empty_time(binding.campus, binding.building, binding.room)
            
            message = (
                f"您绑定的宿舍电量信息：\n"
                f"校区：{binding.campus}\n"
                f"楼栋：{binding.building}\n"
                f"房间：{binding.room}\n"
                f"剩余电量：{electricity_info.value} 度\n"
            )
            
            # 如果有预测结果，添加到消息中
            if empty_time:
                message += f"预计电量耗尽时间：{empty_time.strftime('%Y-%m-%d %H:%M')}\n"
            
            await query_command.finish(message)
            return
        else:
            params = args_text.split()
            if len(params) == 1:
                # 查看校区对应的宿舍楼列表
                campus = params[0]
                if campus not in csust_api.get_campus_names():
                    await query_command.finish(
                        "校区名称错误，请检查输入\nTips：校区名称为「金盆岭」或「云塘」"
                    )
                    return
                buildings = csust_api.get_buildings(campus)
                message = f"{campus}校区的宿舍楼有：\n"
                for building in buildings:
                    message += f"{building}\n"
                await query_command.finish(message)
                return
            elif len(params) == 3:
                # 查询特定宿舍电量
                campus, building, room = params
                if campus not in csust_api.get_campus_names():
                    await query_command.finish(
                        "校区名称错误，请检查输入\nTips：校区名称为「金盆岭」或「云塘」"
                    )
                    return
                if building not in csust_api.get_buildings(campus):
                    await query_command.finish(
                        "楼栋名称错误，请检查输入\nTips：发送「电量 校区」可以查看校区宿舍楼"
                    )
                    return
                electricity_info = csust_api.get_electricity(campus, building, room)
                update_electricity_history(electricity_info, campus, building, room)
                
                # 预测电量耗尽时间
                empty_time = predict_empty_time(campus, building, room)
                
                message = f"{campus}校区 {building} {room} 的剩余电量为：{electricity_info.value}度"
                
                # 如果有预测结果，添加到消息中
                if empty_time:
                    message += f"\n预计电量耗尽时间：{empty_time.strftime('%Y-%m-%d %H:%M')}"
                
                await query_command.finish(message)
                return
            else:
                await query_command.finish("参数数量错误，正确格式：电量 [校区] [楼栋] [房间号] 或 电量 [校区]")
                return
    except FinishedException as e:
        pass
    except Exception as e:
        await query_command.finish(f"查询出错：{str(e)}")
        return


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
