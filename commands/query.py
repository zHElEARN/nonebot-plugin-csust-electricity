from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, Message
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from nonebot.rule import to_me

from ..csust_api import csust_api
from ..utils.common import get_binding, get_sender_info, validate_campus_building
from ..utils.electricity import query_electricity

query_command = on_command("电量", rule=to_me())


@query_command.handle()
async def handle_query(event: Event, args: Message = CommandArg()):
    try:
        sender_type, id = get_sender_info(event)

        args_text = args.extract_plain_text().strip()
        if not args_text:
            # 绑定宿舍查询
            binding = get_binding(sender_type, id)
            if not binding:
                await query_command.finish(
                    "您还没有绑定宿舍，请先使用命令绑定宿舍\n"
                    "格式：/绑定 [校区] [楼栋] [房间号]"
                )
                return

            electricity_info, empty_time = query_electricity(
                binding.campus, binding.building, binding.room
            )

            message = (
                f"您绑定的宿舍电量信息：\n"
                f"校区：{binding.campus}\n"
                f"楼栋：{binding.building}\n"
                f"房间：{binding.room}\n"
                f"剩余电量：{electricity_info.value} 度"
            )

            # 如果有预测结果，添加到消息中
            if empty_time:
                message += (
                    f"\n预计电量耗尽时间：{empty_time.strftime('%Y-%m-%d %H:%M')}"
                )

            await query_command.finish(message)
        else:
            params = args_text.split()
            if len(params) == 1:
                # 查看校区对应的宿舍楼列表
                campus = params[0]

                is_valid, error_msg = validate_campus_building(campus)
                if not is_valid:
                    await query_command.finish(error_msg)
                    return

                buildings = csust_api.get_buildings(campus)
                message = f"{campus}校区的宿舍楼有：\n"
                for building in buildings:
                    message += f"{building}\n"
                await query_command.finish(message)
            elif len(params) == 3:
                # 查询特定宿舍电量
                campus, building, room = params

                is_valid, error_msg = validate_campus_building(campus, building)
                if not is_valid:
                    await query_command.finish(error_msg)
                    return

                electricity_info, empty_time = query_electricity(campus, building, room)

                message = f"{campus}校区 {building} {room} 的剩余电量为：{electricity_info.value}度"

                # 如果有预测结果，添加到消息中
                if empty_time:
                    message += (
                        f"\n预计电量耗尽时间：{empty_time.strftime('%Y-%m-%d %H:%M')}"
                    )

                await query_command.finish(message)
            else:
                await query_command.finish(
                    "参数数量错误，正确格式：/电量 [校区] [楼栋] [房间号] 或 /电量 [校区]"
                )
    except FinishedException:
        pass
    except Exception as e:
        await query_command.finish(f"查询出错：{str(e)}")
