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

from ..csust_api import csust_api
from ..db.electricity_db import Binding, SessionLocal

bind_command = on_command("绑定", rule=to_me())
unbind_command = on_command("解绑", rule=to_me())


@bind_command.handle()
async def handle_bind(event: Event, args: Message = CommandArg()):
    try:
        if isinstance(event, PrivateMessageEvent):
            sender_type = "user"
            id = str(event.get_user_id())
        elif isinstance(event, GroupMessageEvent):
            sender_type = "group"
            id = str(event.group_id)
        else:
            await bind_command.finish("不支持的信息类型")
            return
        args_text = args.extract_plain_text().strip()
        params = args_text.split()
        if len(params) != 3:
            await bind_command.finish("绑定宿舍的格式为：绑定 [校区] [宿舍楼] [宿舍号]")
            return
        campus, building, room = params
        if campus not in csust_api.get_campus_names():
            await bind_command.finish(
                "校区名称错误，请检查输入\nTips：校区名称为「金盆岭」或「云塘」"
            )
            return
        if building not in csust_api.get_buildings(campus):
            await bind_command.finish(
                "楼栋名称错误，请检查输入\nTips：发送「电量 校区」可以查看校区宿舍楼"
            )
            return
        with SessionLocal() as session:
            existing_binding = None
            if sender_type == "group":
                existing_binding = (
                    session.query(Binding).filter(Binding.group_number == id).first()
                )
            else:
                existing_binding = (
                    session.query(Binding).filter(Binding.qq_number == id).first()
                )
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
                f"绑定成功：{campus} {building} {room}\nTips：发送「电量」可以查询宿舍电量"
            )
            return
    except FinishedException as e:
        pass
    except Exception as e:
        await bind_command.finish(f"绑定出错: {str(e)}")
        return


@unbind_command.handle()
async def handle_unbind(event: Event, args: Message = CommandArg()):
    try:
        if isinstance(event, PrivateMessageEvent):
            sender_type = "user"
            id = str(event.get_user_id())
        elif isinstance(event, GroupMessageEvent):
            sender_type = "group"
            id = str(event.group_id)
        else:
            await unbind_command.finish("不支持的信息类型")
            return
        with SessionLocal() as session:
            existing_binding = None
            if sender_type == "group":
                existing_binding = (
                    session.query(Binding).filter(Binding.group_number == id).first()
                )
            else:
                existing_binding = (
                    session.query(Binding).filter(Binding.qq_number == id).first()
                )
            if existing_binding is None:
                await unbind_command.finish(
                    f"{'群组' if sender_type == 'group' else '用户'}未绑定宿舍"
                )
                return
            session.delete(existing_binding)
            session.commit()
            await unbind_command.finish("解绑成功")
            return
    except FinishedException as e:
        pass
    except Exception as e:
        await unbind_command.finish(f"解绑出错: {str(e)}")
        return
