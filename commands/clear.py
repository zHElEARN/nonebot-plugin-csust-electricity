from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Event
from nonebot.exception import FinishedException

from ..db.electricity_db import ElectricityHistory, SessionLocal
from ..utils.common import get_binding, get_sender_info


clear_command = on_command("清除历史", rule=to_me())


@clear_command.handle()
async def handle_clear(event: Event):
    try:
        sender_type, id = get_sender_info(event)

        binding = get_binding(sender_type, id)
        if not binding:
            await clear_command.finish(
                "您还没有绑定宿舍，请先使用命令绑定宿舍\n"
                "格式：/绑定 [校区] [楼栋] [房间号]"
            )
            return

        with SessionLocal() as session:
            session.query(ElectricityHistory).filter(
                ElectricityHistory.campus == binding.campus,
                ElectricityHistory.building == binding.building,
                ElectricityHistory.room == binding.room,
            ).delete()
            session.commit()

            await clear_command.finish("历史电量记录已清除")
    except FinishedException:
        pass
    except Exception as e:
        await clear_command.finish(f"清除历史记录时发生错误：{str(e)}")
