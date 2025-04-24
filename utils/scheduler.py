from nonebot import get_bot, require
from nonebot.log import logger

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

from ..db.electricity_db import Binding, Schedule, SessionLocal
from ..utils.electricity import query_electricity


async def query_and_send(binding_id: str):
    """查询电量并发送消息"""
    try:
        with SessionLocal() as session:
            binding = session.query(Binding).filter(Binding.id == binding_id).first()
            if not binding:
                logger.warning(f"定时任务: 绑定ID {binding_id} 不存在")
                return

        # 使用工具函数获取电量信息和预测时间
        electricity_info, empty_time = query_electricity(
            binding.campus, binding.building, binding.room
        )

        # 构建消息
        message = (
            f"【定时查询】宿舍电量信息：\n"
            f"校区：{binding.campus}\n"
            f"楼栋：{binding.building}\n"
            f"房间：{binding.room}\n"
            f"剩余电量：{electricity_info.value} 度"
        )

        # 如果有预测结果，添加到消息中
        if empty_time:
            message += f"\n预计电量耗尽时间：{empty_time.strftime('%Y-%m-%d %H:%M')}"

        bot = get_bot()
        # 发送消息
        if binding.qq_number:
            await bot.send_private_msg(user_id=int(binding.qq_number), message=message)
        elif binding.group_number:
            await bot.send_group_msg(
                group_id=int(binding.group_number), message=message
            )

        logger.info(
            f"定时任务: 已发送电量信息给 {binding.qq_number or binding.group_number}"
        )
    except Exception as e:
        logger.error(f"定时任务执行失败: {str(e)}")


def init_scheduler():
    """初始化定时任务"""
    logger.info("正在初始化电量查询定时任务...")

    # 获取所有定时任务设置
    with SessionLocal() as session:
        schedules = session.query(Schedule).all()

    # 为每个定时任务创建一个job
    for schedule in schedules:
        hour, minute = schedule.schedule_time.split(":")
        job_id = f"electricity_query_{schedule.binding_id}"

        # 删除已存在的同名任务
        try:
            scheduler.remove_job(job_id)
        except:
            pass

        # 添加新任务
        scheduler.add_job(
            query_and_send,
            "cron",
            hour=int(hour),
            minute=int(minute),
            id=job_id,
            args=[schedule.binding_id],
        )
        logger.info(
            f"已设置定时任务: {schedule.schedule_time} 查询绑定ID {schedule.binding_id}"
        )

    logger.info(f"定时任务初始化完成, 共设置了 {len(schedules)} 个定时任务")


def add_schedule_job(binding_id: str, time_str: str):
    """添加一个定时任务"""
    hour, minute = time_str.split(":")
    job_id = f"electricity_query_{binding_id}"

    # 删除可能存在的同名任务
    try:
        scheduler.remove_job(job_id)
    except:
        pass

    # 添加新任务
    scheduler.add_job(
        query_and_send,
        "cron",
        hour=int(hour),
        minute=int(minute),
        id=job_id,
        args=[binding_id],
    )
    logger.info(f"已添加定时任务: {time_str} 查询绑定ID {binding_id}")


def remove_schedule_job(binding_id: str):
    """移除一个定时任务"""
    job_id = f"electricity_query_{binding_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"已移除定时任务: 查询绑定ID {binding_id}")
        return True
    except:
        logger.warning(f"移除定时任务失败: 查询绑定ID {binding_id} 的任务不存在")
        return False
