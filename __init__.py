import os
import json
import time
import numpy
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import LinearRegression

import nonebot
from nonebot import get_plugin_config, on_command, require, logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import (
    MessageSegment,
    Event,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg

require("nonebot_plugin_txt2img")
from nonebot_plugin_txt2img import Txt2Img

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

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


def ensure_data_folder_exists():
    if not os.path.exists("data"):
        os.makedirs("data")


building_data = fetch_building_data()
binding_data = {}
query_limit_data = {}
scheduled_tasks = {}
electricity_data = {}


def load_binding_data():
    global binding_data
    try:
        with open("data/binding_data.json", "r", encoding="utf-8") as f:
            binding_data = json.load(f)
    except FileNotFoundError:
        binding_data = {}


def save_binding_data():
    with open("data/binding_data.json", "w", encoding="utf-8") as f:
        json.dump(binding_data, f, ensure_ascii=False, indent=4)


def load_scheduled_tasks():
    global scheduled_tasks
    try:
        with open("data/scheduled_tasks.json", "r", encoding="utf-8") as f:
            scheduled_tasks = json.load(f)
    except FileNotFoundError:
        scheduled_tasks = {}


def save_scheduled_tasks():
    with open("data/scheduled_tasks.json", "w", encoding="utf-8") as f:
        json.dump(scheduled_tasks, f, ensure_ascii=False, indent=4)


def load_query_limit_data():
    global query_limit_data
    try:
        with open("data/query_limit_data.json", "r", encoding="utf-8") as f:
            query_limit_data = json.load(f)
    except FileNotFoundError:
        query_limit_data = {}


def save_query_limit_data():
    with open("data/query_limit_data.json", "w", encoding="utf-8") as f:
        json.dump(query_limit_data, f, ensure_ascii=False, indent=4)


def load_electricity_data():
    global electricity_data
    try:
        with open("data/electricity_data.json", "r", encoding="utf-8") as f:
            electricity_data = json.load(f)
    except FileNotFoundError:
        electricity_data = {}


def save_electricity_data():
    with open("data/electricity_data.json", "w", encoding="utf-8") as f:
        json.dump(electricity_data, f, ensure_ascii=False, indent=4)


def store_electricity_data(campus, building_name, room_id, remaining_power):
    load_electricity_data()
    room_key = f"{campus}-{building_name}-{room_id}"
    timestamp = datetime.now().isoformat()
    new_entry = {"timestamp": timestamp, "electricity": remaining_power}

    if (
        room_key not in electricity_data
        or electricity_data[room_key][-1]["electricity"] != remaining_power
    ):
        if room_key not in electricity_data:
            electricity_data[room_key] = []
        electricity_data[room_key].append(new_entry)
        save_electricity_data()

    if len(electricity_data[room_key]) >= 2:
        estimated_time = estimate_discharging_time(electricity_data[room_key])
        if estimated_time:
            return estimated_time

    return None


def estimate_discharging_time(electricity_records):
    if len(electricity_records) < 2:
        return None

    timestamps = [
        datetime.fromisoformat(record["timestamp"]).timestamp()
        for record in electricity_records
    ]
    electricity = [
        float(record["electricity"].split()[0]) for record in electricity_records
    ]

    x = numpy.array(timestamps).reshape(-1, 1)
    y = numpy.array(electricity).reshape(-1, 1)

    model = LinearRegression().fit(x, y)
    predicted_time_seconds = (model.intercept_ / -model.coef_)[0][0]

    predicted_datetime = datetime.fromtimestamp(predicted_time_seconds)
    return predicted_datetime


ensure_data_folder_exists()

load_binding_data()
load_scheduled_tasks()
load_query_limit_data()
load_electricity_data()

# 创建命令
electricity = on_command(
    "电量", aliases={"电量查询", "查电量", "查询电量"}, rule=to_me()
)
bind_room = on_command("绑定宿舍", aliases={"绑定"}, rule=to_me())
unbind_room = on_command("解绑宿舍", aliases={"解绑"}, rule=to_me())
schedule_query = on_command("定时查询", aliases={"设置定时查询"}, rule=to_me())
cancel_schedule = on_command("取消定时查询", rule=to_me())
help_command = on_command("帮助", aliases={"help"}, rule=to_me())


@help_command.handle()
async def handle_help():
    help_text = """
    机器人使用帮助：
    1. 查询电量：
       发送“/电量 校区 宿舍楼 宿舍号”来查询电量
       可以通过输入“/电量 校区”来查看对应校区的宿舍楼
       例如：/电量 云塘 至诚轩5栋A区 A233
       
    2. 绑定宿舍：
       发送“/绑定宿舍 校区 宿舍楼 宿舍号”来绑定宿舍
       例如：/绑定宿舍 云塘 16栋A区 A101
       （绑定之后可以直接发送“/电量”进行查询）
       
    3. 解绑宿舍：
       在群聊中和私聊中均可发送“/解绑”来解绑宿舍
       
    4. 定时查询：
       发送“/定时查询 HH:MM”来设置定时查询
       例如：/定时查询 08:00
       
    5. 取消定时查询：
       在群聊中和私聊中均可发送“/取消定时查询”来取消定时提醒
    """

    # 创建图片
    pic = Txt2Img().draw("机器人帮助", help_text)

    # 发送图片消息
    await help_command.send(MessageSegment.image(pic))


@schedule_query.handle()
async def handle_schedule_query(event: Event, args: Message = CommandArg()):
    if isinstance(event, PrivateMessageEvent):
        user_id = f"user-{event.get_user_id()}"
    elif isinstance(event, GroupMessageEvent):
        user_id = f"group-{event.group_id}"

    time_str = args.extract_plain_text().strip()

    # 校验时间格式
    try:
        query_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await schedule_query.finish("时间格式错误，请使用 例如：定时查询 08:00")

    # 检查用户是否绑定宿舍
    if user_id not in binding_data:
        await schedule_query.finish("请先绑定宿舍信息，再设置定时查询")

    # 设置或更新定时任务
    if user_id in scheduled_tasks:
        scheduler.remove_job(job_id=user_id)

    # 创建定时任务
    scheduler.add_job(
        func=execute_scheduled_query,
        trigger="cron",
        hour=query_time.hour,
        minute=query_time.minute,
        id=user_id,
        args=[user_id],
        replace_existing=True,
    )

    # 保存用户的查询时间
    scheduled_tasks[user_id] = time_str
    save_scheduled_tasks()
    await schedule_query.finish(
        f"已成功设置定时查询，每天 {time_str} 自动查询您的宿舍电量"
    )


@cancel_schedule.handle()
async def handle_cancel_schedule(event: Event):
    if isinstance(event, PrivateMessageEvent):
        user_id = f"user-{event.get_user_id()}"
    elif isinstance(event, GroupMessageEvent):
        user_id = f"group-{event.group_id}"

    if user_id in scheduled_tasks:
        scheduler.remove_job(job_id=user_id)
        del scheduled_tasks[user_id]
        save_scheduled_tasks()
        await cancel_schedule.finish("已成功取消您的定时查询任务")
    else:
        await cancel_schedule.finish("您没有设置定时查询任务")


async def execute_scheduled_query(user_id: str):
    if user_id not in binding_data:
        return

    campus, building_name, room_id = binding_data[user_id]
    electricity_data = fetch_electricity_data(
        campus, building_data[campus][building_name], room_id
    )

    if electricity_data and "剩余电量" in electricity_data:
        remaining_power = electricity_data["剩余电量"]
        msg = f"定时查询提醒：\n{campus}校区 {building_name} {room_id} 的剩余电量为：{remaining_power}"

        estimated_time = store_electricity_data(
            campus, building_name, room_id, remaining_power
        )

        if estimated_time:
            estimated_time_str = estimated_time.strftime("%Y-%m-%d %H:%M:%S")
            msg += f"\n预计电量耗尽时间：{estimated_time_str}"

        # 根据用户ID前缀选择私聊或群聊发送
        if user_id.startswith("user-"):
            await nonebot.get_bot().send_private_msg(
                user_id=int(user_id.split("-")[1]), message=msg
            )
        elif user_id.startswith("group-"):
            await nonebot.get_bot().send_group_msg(
                group_id=int(user_id.split("-")[1]), message=msg
            )


# 加载定时任务到scheduler
def load_tasks_to_scheduler():
    for user_id, time_str in scheduled_tasks.items():
        query_time = datetime.strptime(time_str, "%H:%M").time()
        scheduler.add_job(
            func=execute_scheduled_query,
            trigger="cron",
            hour=query_time.hour,
            minute=query_time.minute,
            id=user_id,
            args=[user_id],
            replace_existing=True,
        )


# 初始化加载定时任务
load_tasks_to_scheduler()


@electricity.handle()
async def handle_electricity(event: Event, args: Message = CommandArg()):
    if isinstance(event, PrivateMessageEvent):
        user_id = f"user-{event.get_user_id()}"
    elif isinstance(event, GroupMessageEvent):
        user_id = f"group-{event.group_id}"

    args_text = args.extract_plain_text().strip()

    # 检查查询次数限制
    if isinstance(event, GroupMessageEvent) and args_text:
        # 处理用户提供参数查询电量
        query_limit_identifier = f"user-{event.get_user_id()}"
    else:
        # 处理普通绑定查询电量
        query_limit_identifier = user_id

    if not check_query_limit(query_limit_identifier):
        await electricity.finish("查询次数已达上限，每小时最多查询两次。请稍后再试")

    # 检查用户是否提供了查询参数
    if not args_text:
        if user_id in binding_data:
            campus, building_name, room_id = binding_data[user_id]
            await query_electricity(
                campus, building_name, room_id, electricity, query_limit_identifier
            )
        else:
            await electricity.finish(
                "未检测到绑定信息，请先绑定宿舍，或直接使用命令指定宿舍"
            )
    else:
        parts = args_text.split()
        if len(parts) == 1:
            campus = parts[0]
            if campus in building_data:
                buildings = "\n".join(building_data[campus].keys())
                pic = Txt2Img().draw(f"{campus}的宿舍楼列表", buildings)
                await electricity.finish(MessageSegment.image(pic))
            else:
                await electricity.finish(
                    "校区名称错误，请输入有效的校区（如：云塘、金盆岭）"
                )
        elif len(parts) == 3:
            campus, building_name, room_id = parts
            await query_electricity(
                campus, building_name, room_id, electricity, query_limit_identifier
            )
        else:
            await electricity.finish(
                "请输入正确的格式：\n1. 查询校区宿舍楼：电量 云塘\n2. 查询电量：电量 云塘 16栋A区 A101"
            )


async def query_electricity(
    campus, building_name, room_id, handler, query_limit_identifier
):
    if campus not in building_data or building_name not in building_data[campus]:
        await handler.finish("校区或宿舍楼名称错误，请检查输入")

    building_id = building_data[campus][building_name]
    new_electricity_data = fetch_electricity_data(campus, building_id, room_id)

    if new_electricity_data and "剩余电量" in new_electricity_data:
        remaining_power = new_electricity_data["剩余电量"]
        update_query_limit(query_limit_identifier)  # 更新查询记录

        # 保存电量数据
        estimated_time = store_electricity_data(
            campus, building_name, room_id, remaining_power
        )

        msg = f"{campus}校区 {building_name} {room_id} 的剩余电量为：{remaining_power}"
        if estimated_time:
            estimated_time_str = estimated_time.strftime("%Y-%m-%d %H:%M:%S")
            msg += f"\n预计电量耗尽时间：{estimated_time_str}"
        await handler.finish(msg)
    else:
        await handler.finish("未能获取电量信息，请检查宿舍号是否正确")


def check_query_limit(identifier):
    current_time = time.time()
    if identifier in query_limit_data:
        last_time, count = query_limit_data[identifier]
        # 若在一小时内查询次数达到两次
        if current_time - last_time < 3600 and count >= 2:
            return False
        # 若超过一小时，则重置查询次数
        elif current_time - last_time >= 3600:
            query_limit_data[identifier] = (current_time, 0)
            save_query_limit_data()
            return True
    else:
        query_limit_data[identifier] = (current_time, 0)
        save_query_limit_data()
    return True


def update_query_limit(identifier):
    current_time = time.time()
    if identifier in query_limit_data:
        last_time, count = query_limit_data[identifier]
        if current_time - last_time < 3600:
            query_limit_data[identifier] = (last_time, count + 1)
        else:
            query_limit_data[identifier] = (current_time, 1)
    else:
        query_limit_data[identifier] = (current_time, 1)
    save_query_limit_data()


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

    binding_data[user_id] = [campus, building_name, room_id]
    save_binding_data()
    await bind_room.finish(
        f"绑定成功！已将{'您的QQ号' if 'user-' in user_id else '本群号'}与{campus}校区 {building_name} {room_id} 绑定"
    )


@unbind_room.handle()
async def handle_unbind_room(event: Event):
    if isinstance(event, PrivateMessageEvent):
        user_id = f"user-{event.get_user_id()}"
    elif isinstance(event, GroupMessageEvent):
        user_id = f"group-{event.group_id}"

    if user_id in binding_data:
        del binding_data[user_id]
        save_binding_data()
        await unbind_room.finish("解绑成功，已解除您的宿舍绑定信息")
    else:
        await unbind_room.finish("您未绑定宿舍信息，无需解绑")
