import requests
import logging
from config import ENABLE_WHITE_LIST, GROUP_MSG_API, PREFIX, WHITE_LISTED_GROUPS
from commands import (
    handle_invalid_command,
    handle_query_command,
    handle_bind_command,
    handle_buildings_command,
    list_commands,
)

logger = logging.getLogger(__name__)


def send_group_message(group_id, message):
    data = {"group_id": group_id, "message": message}
    try:
        response = requests.post(GROUP_MSG_API, json=data)
        response.raise_for_status()
        logger.info(f"发送消息到群 {group_id}: {message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"发送消息失败: {e}")


async def handle_message(data):
    if data.get("post_type") == "message" and data.get("message_type") == "group":
        group_id = data.get("group_id")
        raw_message = data.get("raw_message", "").strip()
        logger.info(f"收到来自群 {group_id} 的消息: {raw_message}")

        if ENABLE_WHITE_LIST and group_id not in WHITE_LISTED_GROUPS:
            logger.info(f"Group {group_id} is not in the white list, message ignored.")
            return

        if raw_message.startswith(PREFIX):
            command_parts = raw_message[len(PREFIX) :].split()
            if not command_parts:
                return

            command = command_parts[0]
            if command == "help":
                response = list_commands()
                send_group_message(group_id, response)

            elif command == "query":
                response = handle_query_command(group_id)
                send_group_message(group_id, response)

            elif command == "bind" and len(command_parts) > 3:
                area, building_id, room_id = (
                    command_parts[1],
                    command_parts[2],
                    command_parts[3],
                )
                response = handle_bind_command(group_id, area, building_id, room_id)
                send_group_message(group_id, response)

            elif command == "buildings" and len(command_parts) > 1:
                area = command_parts[1]
                response = handle_buildings_command(area)
                send_group_message(group_id, response)

            else:
                response = handle_invalid_command()
                send_group_message(group_id, response)
                logger.warning(f"无效指令: {raw_message}")
