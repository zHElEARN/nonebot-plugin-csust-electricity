from ..csust_api import building_data
from ..data_manager import data_manager

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Event, Message, GroupMessageEvent, PrivateMessageEvent

bind_room = on_command("绑定宿舍", aliases={"绑定"}, rule=to_me())
unbind_room = on_command("解绑宿舍", aliases={"解绑"}, rule=to_me())

@bind_room.handle()
async def handle_bind_room(event: Event, args: Message = CommandArg()):
    if isinstance(event, PrivateMessageEvent):
        user_id = f"user-{event.get_user_id()}"
    elif isinstance(event, GroupMessageEvent):
        user_id = f"group-{event.group_id}"

    args_text = args.extract_plain_text().strip()
    parts = args_text.split()

    if len(parts) != 3:
        await bind_room.finish(
            "绑定宿舍的格式为：绑定宿舍 校区 宿舍楼 宿舍号\n例如：绑定宿舍 云塘 16栋A区 A101"
        )

    campus, building_name, room_id = parts
    if campus not in building_data or building_name not in building_data[campus]:
        await bind_room.finish("校区或宿舍楼名称错误，请检查输入")

    data_manager.binding_data[user_id] = [campus, building_name, room_id]
    data_manager.save_binding_data()
    await bind_room.finish(
        f"绑定成功！已将{'您的QQ号' if 'user-' in user_id else '本群号'}与{campus}校区 {building_name} {room_id} 绑定"
    )


@unbind_room.handle()
async def handle_unbind_room(event: Event):
    if isinstance(event, PrivateMessageEvent):
        user_id = f"user-{event.get_user_id()}"
    elif isinstance(event, GroupMessageEvent):
        user_id = f"group-{event.group_id}"

    if user_id in data_manager.binding_data:
        del data_manager.binding_data[user_id]
        data_manager.save_binding_data()
        await unbind_room.finish("解绑成功，已解除您的宿舍绑定信息")
    else:
        await unbind_room.finish("您未绑定宿舍信息，无需解绑")
