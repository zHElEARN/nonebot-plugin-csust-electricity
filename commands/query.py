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

from ..csust_api import ElectricityInfo, csust_api
from ..db.electricity_db import Binding, ElectricityHistory, SessionLocal

query_command = on_command("电量", rule=to_me())


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
            message = (
                f"您绑定的宿舍电量信息：\n"
                f"校区：{binding.campus}\n"
                f"楼栋：{binding.building}\n"
                f"房间：{binding.room}\n"
                f"剩余电量：{electricity_info.value} 度\n"
            )
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
                message = f"{campus}校区 {building} {room} 的剩余电量为：{electricity_info.value}度"
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
