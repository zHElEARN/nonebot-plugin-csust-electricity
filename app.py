import requests
import json
import time
from datetime import datetime
import asyncio
import websockets
from urllib.parse import urlencode

# 常量定义
PREFIX = "."  # 指令前缀
WHITE_LISTED_GROUPS = [966613029]  # 群号白名单
BINDINGS_FILE = "bindings.json"  # 持久化文件路径

# 电费查询API的设置
url = "http://yktwd.csust.edu.cn:8988/web/Common/Tsm.html"
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

# 绑定信息加载/保存功能
def load_bindings():
    """加载持久化的群号和宿舍绑定信息"""
    try:
        with open(BINDINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_bindings():
    """保存群号和宿舍绑定信息到文件"""
    with open(BINDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_bindings, f, ensure_ascii=False, indent=4)

# 加载初始绑定信息
user_bindings = load_bindings()

# 将电费查询参数作为字典模板
query_params_template = {
    "jsondata": {
        "query_elec_roominfo": {
            "aid": "0030000000002501",
            "account": "317064",
            "room": {"roomid": "", "room": ""},
            "floor": {"floorid": "", "floor": ""},
            "area": {"area": "云塘校区", "areaname": "云塘校区"},
            "building": {"buildingid": "557", "building": "至诚轩5栋A区"}
        }
    },
    "funname": "synjones.onecard.query.elec.roominfo",
    "json": "true"
}

# 手动转换字典为URL编码的表单数据格式
def dict_to_urlencoded(data):
    return urlencode({"jsondata": json.dumps(data["jsondata"]), "funname": data["funname"], "json": data["json"]})

# 消息发送API和方法
GROUP_MSG_API = "http://192.168.5.5:3000/send_group_msg"

def send_group_message(group_id, message):
    data = {
        "group_id": group_id,
        "message": message
    }
    try:
        response = requests.post(GROUP_MSG_API, json=data)
        response.raise_for_status()
        print(f"Message sent successfully: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

# 查询电费的函数
def query_electricity(room_id):
    try:
        # 更新查询参数的房间号
        query_params = query_params_template.copy()
        query_params["jsondata"]["query_elec_roominfo"]["room"]["roomid"] = room_id
        query_params["jsondata"]["query_elec_roominfo"]["room"]["room"] = room_id

        # 将字典转换为URL编码的字符串格式
        encoded_data = dict_to_urlencoded(query_params)

        # 发送POST请求
        response = requests.post(url, headers=headers, data=encoded_data)
        response.raise_for_status()

        # 解析返回的JSON数据
        result = response.json()
        info = result.get("query_elec_roominfo", {})

        # 提取宿舍信息和电量信息
        room = info.get("room", {}).get("room", "未知宿舍")
        electricity = info.get("errmsg", "未知电量")

        # 获取当前查询时间
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 格式化输出内容
        message = f"查询时间：{query_time}\n宿舍：{room}\n剩余电量：{electricity}"
        print(message)

        return message

    except requests.exceptions.RequestException as e:
        print("查询失败，网络请求错误：", e)
        return "查询失败，网络请求错误"
    except json.JSONDecodeError:
        print("查询失败，无法解析响应数据")
        return "查询失败，无法解析响应数据"

# WebSocket连接的设置
WS_URL = "ws://192.168.5.5:3001"

async def listen_to_messages():
    async with websockets.connect(WS_URL) as websocket:
        print("WebSocket连接已建立，开始监听消息...")

        while True:
            # 等待接收消息
            message = await websocket.recv()
            data = json.loads(message)

            # 检查是否为群聊消息，并核对group_id
            if data.get("post_type") == "message" and data.get("message_type") == "group":
                group_id = data.get("group_id")
                raw_message = data.get("raw_message").strip()

                # 检查群号是否在白名单中
                if group_id in WHITE_LISTED_GROUPS:
                    print(f"收到群组消息：{raw_message}")

                    # 检查指令前缀并确保指令长度大于前缀
                    if raw_message.startswith(PREFIX) and len(raw_message) > len(PREFIX):
                        command = raw_message[len(PREFIX):].split()

                        if command[0] == "df":
                            # 获取绑定宿舍信息
                            room_id = user_bindings.get(str(group_id))
                            if room_id:
                                # 查询绑定宿舍的电费并发送
                                electricity_info = query_electricity(room_id)
                                send_group_message(group_id=group_id, message=electricity_info)
                            else:
                                # 提示用户尚未绑定宿舍
                                send_group_message(group_id=group_id, message="尚未绑定宿舍，请先使用 .bd 命令绑定宿舍")

                        elif command[0] == "bd" and len(command) > 1:
                            # 绑定宿舍指令
                            room_id = command[1]
                            user_bindings[str(group_id)] = room_id
                            save_bindings()  # 更新持久化文件
                            send_group_message(group_id=group_id, message=f"宿舍 {room_id} 绑定成功！")

# 主函数运行WebSocket监听
async def main():
    await listen_to_messages()

# 启动机器人
if __name__ == "__main__":
    asyncio.run(main())
