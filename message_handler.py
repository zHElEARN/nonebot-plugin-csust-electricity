# message_handler.py

import requests
from config import GROUP_MSG_API, PREFIX, WHITE_LISTED_GROUPS
from commands import handle_df_command, handle_bd_command

def send_group_message(group_id, message):
    data = {
        "group_id": group_id,
        "message": message
    }
    try:
        response = requests.post(GROUP_MSG_API, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

async def handle_message(data):
    if data.get("post_type") == "message" and data.get("message_type") == "group":
        group_id = data.get("group_id")
        raw_message = data.get("raw_message", "").strip()

        if group_id in WHITE_LISTED_GROUPS and raw_message.startswith(PREFIX):
            command_parts = raw_message[len(PREFIX):].split()
            if not command_parts:
                return

            if command_parts[0] == "df":
                response = handle_df_command(group_id)
                send_group_message(group_id, response)

            elif command_parts[0] == "bd" and len(command_parts) > 1:
                room_id = command_parts[1]
                response = handle_bd_command(group_id, room_id)
                send_group_message(group_id, response)
