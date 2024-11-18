from ..data_manager import data_manager
from ..utils import store_electricity_data
from ..csust_api import fetch_electricity_data, building_data

import nonebot
from nonebot import on_command, require, logger
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Event,
    Message,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from datetime import datetime

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

data_manager.load_scheduled_tasks()


def load_tasks_to_scheduler():
    for prefix in ["user", "group"]:
        for id, time_str in data_manager.scheduled_tasks[prefix].items():
            identity = f"{prefix}-{id}"
            query_time = datetime.strptime(time_str, "%H:%M").time()
            scheduler.add_job(
                func=execute_scheduled_query,
                trigger="cron",
                hour=query_time.hour,
                minute=query_time.minute,
                id=identity,
                args=[prefix, id],
                replace_existing=True,
            )


async def execute_scheduled_query(prefix, id):
    if id not in data_manager.binding_data[prefix]:
        return

    campus, building_name, room_id = data_manager.binding_data[prefix][id]
    remaining_power = fetch_electricity_data(
        campus, building_data[campus][building_name], room_id
    )

    if remaining_power != "未知":
        msg = f"定时查询提醒：\n{campus}校区 {building_name} {room_id} 的剩余电量为：{remaining_power}度"

        estimated_time = store_electricity_data(
            campus, building_name, room_id, remaining_power
        )

        if estimated_time:
            estimated_time_str = estimated_time.strftime("%Y-%m-%d %H:%M:%S")
            msg += f"\n预计电量耗尽时间：{estimated_time_str}"

        # 根据用户ID前缀选择私聊或群聊发送
        if prefix == "user":
            await nonebot.get_bot().send_private_msg(user_id=int(id), message=msg)
        elif prefix == "group":
            await nonebot.get_bot().send_group_msg(group_id=int(id), message=msg)


load_tasks_to_scheduler()

schedule_query = on_command("定时查询", aliases={"设置定时查询"}, rule=to_me())
cancel_schedule = on_command("取消定时查询", rule=to_me())


@schedule_query.handle()
async def handle_schedule_query(event: Event, args: Message = CommandArg()):
    if isinstance(event, PrivateMessageEvent):
        prefix = "user"
        id = event.get_user_id()
    elif isinstance(event, GroupMessageEvent):
        prefix = "group"
        id = str(event.group_id)

    identity = f"{prefix}-{id}"

    time_str = args.extract_plain_text().strip()

    # 校验时间格式
    try:
        query_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await schedule_query.finish("时间格式错误，请使用 例如：定时查询 08:00")

    # 检查用户是否绑定宿舍
    if id not in data_manager.binding_data[prefix]:
        await schedule_query.finish("请先绑定宿舍信息，再设置定时查询")

    # 设置或更新定时任务
    if id in data_manager.scheduled_tasks[prefix]:
        scheduler.remove_job(job_id=identity)

    # 创建定时任务
    scheduler.add_job(
        func=execute_scheduled_query,
        trigger="cron",
        hour=query_time.hour,
        minute=query_time.minute,
        id=identity,
        args=[prefix, id],
        replace_existing=True,
    )

    # 保存用户的查询时间
    data_manager.scheduled_tasks[prefix] = {id: time_str}
    data_manager.save_scheduled_tasks()
    await schedule_query.finish(
        f"已成功设置定时查询，每天 {time_str} 自动查询您的宿舍电量"
    )


@cancel_schedule.handle()
async def handle_cancel_schedule(event: Event):
    if isinstance(event, PrivateMessageEvent):
        prefix = "user"
        id = event.get_user_id()
    elif isinstance(event, GroupMessageEvent):
        prefix = "group"
        id = str(event.group_id)

    identity = f"{prefix}-{id}"

    if id in data_manager.scheduled_tasks[prefix]:
        scheduler.remove_job(job_id=identity)
        del data_manager.scheduled_tasks[prefix][id]
        data_manager.save_scheduled_tasks()
        await cancel_schedule.finish("已成功取消您的定时查询任务")
    else:
        await cancel_schedule.finish("您没有设置定时查询任务")
