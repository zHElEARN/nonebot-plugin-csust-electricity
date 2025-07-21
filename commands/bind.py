from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, Message
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from nonebot.rule import to_me

from ..db.electricity_db import Binding, Schedule, SessionLocal
from ..utils.common import get_binding, get_sender_info, validate_campus_building
from ..utils.scheduler import remove_schedule_job

bind_command = on_command("绑定", rule=to_me())
unbind_command = on_command("解绑", rule=to_me())


@bind_command.handle()
async def handle_bind(event: Event, args: Message = CommandArg()):
    try:
        sender_type, id = get_sender_info(event)

        args_text = args.extract_plain_text().strip()
        params = args_text.split()
        if len(params) != 3:
            await bind_command.finish("绑定宿舍的格式为：/绑定 [校区] [宿舍楼] [宿舍号]")
            return

        campus, building, room = params

        is_valid, error_msg = validate_campus_building(campus, building)
        if not is_valid:
            await bind_command.finish(error_msg)
            return

        with SessionLocal() as session:
            existing_binding = get_binding(sender_type, id)

            if existing_binding is not None:
                await bind_command.finish(
                    f"{'群组' if sender_type == 'group' else '用户'}已绑定宿舍：{existing_binding.campus} {existing_binding.building} {existing_binding.room}，请先解绑后再绑定新宿舍"
                )
                return

            if sender_type == "group":
                session.add(
                    Binding(
                        group_number=id,
                        campus=campus,
                        building=building,
                        room=room,
                    )
                )
            else:
                session.add(
                    Binding(qq_number=id, campus=campus, building=building, room=room)
                )

            session.commit()
            await bind_command.finish(
                f"绑定成功：{campus} {building} {room}\nTips：发送「/电量」可以查询宿舍电量"
            )
    except FinishedException:
        pass
    except Exception as e:
        await bind_command.finish(f"绑定出错: {str(e)}")


@unbind_command.handle()
async def handle_unbind(event: Event):
    try:
        sender_type, id = get_sender_info(event)

        existing_binding = get_binding(sender_type, id)
        if existing_binding is None:
            await unbind_command.finish(
                f"{'群组' if sender_type == 'group' else '用户'}未绑定宿舍"
            )
            return

        with SessionLocal() as session:
            # 查询关联的定时任务并删除
            schedule = (
                session.query(Schedule)
                .filter(Schedule.binding_id == existing_binding.id)
                .first()
            )
            if schedule:
                remove_schedule_job(existing_binding.id)

            session.delete(existing_binding)
            session.commit()
            await unbind_command.finish("解绑成功")
    except FinishedException:
        pass
    except Exception as e:
        await unbind_command.finish(f"解绑出错: {str(e)}")
