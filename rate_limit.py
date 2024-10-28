# rate_limit.py

import json
import time
import logging
from config import RATE_LIMIT_FILE, RATE_LIMIT_THRESHOLD, RATE_LIMIT_INTERVAL

logger = logging.getLogger(__name__)


def load_rate_limit_data():
    """加载持久化的限速记录数据"""
    try:
        with open(RATE_LIMIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_rate_limit_data(rate_limit_data):
    """保存限速记录数据到文件"""
    with open(RATE_LIMIT_FILE, "w", encoding="utf-8") as f:
        json.dump(rate_limit_data, f, ensure_ascii=False, indent=4)


def check_rate_limit(group_id):
    """检查指定群是否超出查询限速限制"""
    rate_limit_data = load_rate_limit_data()
    current_time = int(time.time())

    # 获取群的查询记录，初始化为空列表
    group_queries = rate_limit_data.get(str(group_id), [])

    # 过滤出一小时以内的查询记录
    recent_queries = [
        t for t in group_queries if current_time - t < RATE_LIMIT_INTERVAL
    ]
    rate_limit_data[str(group_id)] = recent_queries  # 更新查询记录

    if len(recent_queries) >= RATE_LIMIT_THRESHOLD:
        save_rate_limit_data(rate_limit_data)  # 持久化保存
        logger.warning(f"Group {group_id} has exceeded the rate limit.")
        return False  # 超出限制

    # 记录当前查询
    recent_queries.append(current_time)
    rate_limit_data[str(group_id)] = recent_queries
    save_rate_limit_data(rate_limit_data)  # 持久化保存
    logger.info(f"Group {group_id} query count within limit.")
    return True  # 未超出限制
