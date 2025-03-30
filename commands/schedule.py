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

from ..db.electricity_db import Binding, Schedule, SessionLocal
from ..utils.scheduler import add_schedule_job, init_scheduler, remove_schedule_job

init_scheduler()

schedule_command = on_command("定时查询", rule=to_me())
cancel_schedule_command = on_command("取消定时查询", rule=to_me())


@schedule_command.handle()
async def handle_schedule(event: Event, args: Message = CommandArg()):
    try:
        if isinstance(event, PrivateMessageEvent):
            sender_type = "user"
            id = str(event.get_user_id())
        elif isinstance(event, GroupMessageEvent):
            sender_type = "group"
            id = str(event.group_id)
        else:
            await schedule_command.finish("不支持的消息类型")
            return

        time_arg = args.extract_plain_text().strip()
        if not time_arg:
            await schedule_command.finish(
                "请输入定时时间，格式：定时查询 HH:MM（例如：定时查询 08:00）"
            )
            return

        if not validate_time_format(time_arg):
            await schedule_command.finish(
                "时间格式错误，请使用HH:MM格式（例如：08:00）"
            )
            return

        with SessionLocal() as session:
            if sender_type == "user":
                binding = session.query(Binding).filter(Binding.qq_number == id).first()
            else:
                binding = (
                    session.query(Binding).filter(Binding.group_number == id).first()
                )

            if not binding:
                await schedule_command.finish(
                    "您还没有绑定宿舍，请先使用命令绑定宿舍\n"
                    "格式：绑定 [校区] [楼栋] [房间号]"
                )
                return

            existing_schedule = (
                session.query(Schedule)
                .filter(Schedule.binding_id == binding.id)
                .first()
            )
            if existing_schedule:
                await schedule_command.finish(
                    f"您已设置了定时查询：{existing_schedule.schedule_time}\n"
                    f"如需修改，请先取消现有定时查询"
                )
                return

            new_schedule = Schedule(binding_id=binding.id, schedule_time=time_arg)
            session.add(new_schedule)
            session.commit()

            # 添加定时任务
            add_schedule_job(binding.id, time_arg)

            await schedule_command.finish(
                f"定时查询设置成功，将在每天 {time_arg} 自动查询电量"
            )

    except FinishedException:
        pass
    except Exception as e:
        await schedule_command.finish(f"设置定时查询失败：{str(e)}")


@cancel_schedule_command.handle()
async def handle_cancel_schedule(event: Event, args: Message = CommandArg()):
    try:
        if isinstance(event, PrivateMessageEvent):
            sender_type = "user"
            id = str(event.get_user_id())
        elif isinstance(event, GroupMessageEvent):
            sender_type = "group"
            id = str(event.group_id)
        else:
            await cancel_schedule_command.finish("不支持的消息类型")
            return

        with SessionLocal() as session:
            if sender_type == "user":
                binding = session.query(Binding).filter(Binding.qq_number == id).first()
            else:
                binding = (
                    session.query(Binding).filter(Binding.group_number == id).first()
                )

            if not binding:
                await cancel_schedule_command.finish(
                    "您还没有绑定宿舍，无法取消定时查询"
                )
                return

            schedule = (
                session.query(Schedule)
                .filter(Schedule.binding_id == binding.id)
                .first()
            )
            if not schedule:
                await cancel_schedule_command.finish("您没有设置定时查询")
                return

            # 移除定时任务
            remove_schedule_job(binding.id)

            session.delete(schedule)
            session.commit()

            await cancel_schedule_command.finish("定时查询已取消")

    except FinishedException:
        pass
    except Exception as e:
        await cancel_schedule_command.finish(f"取消定时查询失败：{str(e)}")


def validate_time_format(time_str: str) -> bool:
    try:
        hour, minute = time_str.split(":")
        hour_int, minute_int = int(hour), int(minute)
        return 0 <= hour_int < 24 and 0 <= minute_int < 60
    except (ValueError, TypeError):
        return False
