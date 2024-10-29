import json
from pathlib import Path

import nonebot
from nonebot import get_plugin_config, on_command, require
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, Event
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg

require("nonebot_plugin_txt2img")
from nonebot_plugin_txt2img import Txt2Img

from .config import Config
from .csust_api import fetch_electricity_data, fetch_building_data

__plugin_meta__ = PluginMetadata(
    name="nonebot-csust-electricity",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)

# 加载宿舍楼信息的全局变量
building_data = fetch_building_data()
binding_data = {}

def load_binding_data():
    global binding_data
    try:
        with open("binding_data.json", "r", encoding="utf-8") as f:
            binding_data = json.load(f)
    except FileNotFoundError:
        binding_data = {}

def save_binding_data():
    with open("binding_data.json", "w", encoding="utf-8") as f:
        json.dump(binding_data, f, ensure_ascii=False, indent=4)

load_binding_data()

# 创建“电量”命令
electricity = on_command("电量", aliases={"电量查询", "查电量"}, rule=to_me())
# 创建“绑定宿舍”命令
bind_room = on_command("绑定宿舍", aliases={"绑定"})
# 创建“解绑宿舍”命令
unbind_room = on_command("解绑宿舍", aliases={"解绑"})

@electricity.handle()
async def handle_electricity(event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    args_text = args.extract_plain_text().strip()
    
    # 检查用户是否提供了查询参数
    if not args_text:
        # 用户未提供参数，尝试使用绑定信息查询
        if user_id in binding_data:
            campus, building_name, room_id = binding_data[user_id]
            await query_electricity(campus, building_name, room_id, electricity)
        else:
            await electricity.finish("未检测到绑定信息，请先绑定宿舍，或直接使用命令指定宿舍")
    else:
        # 用户提供了参数，按照参数查询
        parts = args_text.split()
        if len(parts) == 1:
            # 仅提供校区名称，列出所有宿舍楼
            campus = parts[0]
            if campus in building_data:
                buildings = "\n".join(building_data[campus].keys())
                
                pic = Txt2Img().draw(f"{campus}的宿舍楼列表", buildings)
                await electricity.finish(MessageSegment.image(pic))
            else:
                await electricity.finish("校区名称错误，请输入有效的校区（如：云塘、金盆岭）")
        elif len(parts) == 3:
            # 提供了校区、宿舍楼、宿舍号
            campus, building_name, room_id = parts
            await query_electricity(campus, building_name, room_id, electricity)
        else:
            await electricity.finish("请输入正确的格式：\n1. 查询校区宿舍楼：电量 云塘\n2. 查询电量：电量 云塘 16栋A区 A101")

async def query_electricity(campus, building_name, room_id, handler):
    if campus not in building_data:
        await handler.finish("校区名称错误，请输入有效的校区（如：云塘、金盆岭）")
    if building_name not in building_data[campus]:
        await handler.finish(f"{campus}校区中未找到 {building_name} 宿舍楼，请检查输入")
    
    building_id = building_data[campus][building_name]
    electricity_data = fetch_electricity_data(campus, building_id, room_id)
    
    if electricity_data and "剩余电量" in electricity_data:
        remaining_power = electricity_data["剩余电量"]
        await handler.finish(
            f"{campus}校区 {building_name} {room_id} 的剩余电量为：{remaining_power}"
        )
    else:
        await handler.finish("未能获取电量信息，请检查宿舍号是否正确")

@bind_room.handle()
async def handle_bind_room(event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    args_text = args.extract_plain_text().strip()
    parts = args_text.split()
    
    if len(parts) != 3:
        await bind_room.finish("绑定宿舍的格式为：绑定宿舍 校区 宿舍楼 宿舍号\n例如：绑定宿舍 云塘 16栋A区 A101")
    
    campus, building_name, room_id = parts
    if campus not in building_data or building_name not in building_data[campus]:
        await bind_room.finish("校区或宿舍楼名称错误，请检查输入")

    # 保存绑定信息
    binding_data[user_id] = [campus, building_name, room_id]
    save_binding_data()
    await bind_room.finish(f"绑定成功！已将您的QQ号与{campus}校区 {building_name} {room_id} 绑定")

@unbind_room.handle()
async def handle_unbind_room(event: Event):
    user_id = event.get_user_id()
    if user_id in binding_data:
        del binding_data[user_id]
        save_binding_data()
        await unbind_room.finish("解绑成功，已解除您的宿舍绑定信息")
    else:
        await unbind_room.finish("您未绑定宿舍信息，无需解绑")
