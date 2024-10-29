import json
from pathlib import Path

import nonebot
from nonebot import get_plugin_config, on_command
from nonebot.adapters import Message
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg

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

# 创建“电量”命令
electricity = on_command("电量", aliases={"电量查询", "查电量"})

@electricity.handle()
async def handle_electricity(args: Message = CommandArg()):
    args_text = args.extract_plain_text().strip()
    
    # 如果只提供了校区名称，列出所有宿舍楼
    if args_text in building_data:
        campus = args_text
        buildings = "\n".join(building_data[campus].keys())
        await electricity.finish(f"{campus}校区的宿舍楼有：\n{buildings}")
    
    # 如果输入格式为“校区 宿舍楼 宿舍号”
    parts = args_text.split()
    if len(parts) == 3:
        campus, building_name, room_id = parts
        if campus not in building_data:
            await electricity.finish("校区名称错误，请输入有效的校区（如：云塘、金盆岭）")
        if building_name not in building_data[campus]:
            await electricity.finish(f"{campus}校区中未找到 {building_name} 宿舍楼，请检查输入")

        # 获取宿舍楼ID
        building_id = building_data[campus][building_name]
        # 查询电量数据
        electricity_data = fetch_electricity_data(campus, building_id, room_id)
        
        # 检查返回的电量数据并格式化输出
        if electricity_data is not None and "剩余电量" in electricity_data:
            remaining_power = electricity_data["剩余电量"]
            await electricity.finish(
                f"{campus}校区 {building_name} {room_id} 的剩余电量为：{remaining_power}"
            )
        else:
            await electricity.finish("未能获取电量信息，请检查宿舍号是否正确")
    
    # 若输入格式错误
    await electricity.finish("请输入正确的格式：\n1. 查询校区宿舍楼：电量 云塘\n2. 查询电量：电量 云塘 16栋A区 A101")
