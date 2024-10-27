import requests
import json
import time
from datetime import datetime
import asyncio
import websockets

# 电费查询API的设置
url = "http://yktwd.csust.edu.cn:8988/web/Common/Tsm.html"
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}
raw_data = "jsondata=%7B+%22query_elec_roominfo%22%3A+%7B+%22aid%22%3A%220030000000002501%22%2C+%22account%22%3A+%22317064%22%2C%22room%22%3A+%7B+%22roomid%22%3A+%22A544%22%2C+%22room%22%3A+%22A544%22+%7D%2C++%22floor%22%3A+%7B+%22floorid%22%3A+%22%22%2C+%22floor%22%3A+%22%22+%7D%2C+%22area%22%3A+%7B+%22area%22%3A+%22%E4%BA%91%E5%A1%98%E6%A0%A1%E5%8C%BA%22%2C+%22areaname%22%3A+%22%E4%BA%91%E5%A1%98%E6%A0%A1%E5%8C%BA%22+%7D%2C+%22building%22%3A+%7B+%22buildingid%22%3A+%22557%22%2C+%22building%22%3A+%22%E8%87%B3%E8%AF%9A%E8%BD%A95%E6%A0%8BA%E5%8C%BA%22+%7D+%7D+%7D&funname=synjones.onecard.query.elec.roominfo&json=true"

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
def query_electricity():
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, data=raw_data)
        response.raise_for_status()  # 检查请求是否成功

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

                # 仅处理指定群聊的消息
                if group_id == 966613029:
                    print(f"收到群组消息：{raw_message}")

                    # 判断是否为查询电费指令
                    if raw_message == ".df":
                        # 查询电费并发送结果
                        electricity_info = query_electricity()
                        send_group_message(group_id=group_id, message=electricity_info)

# 主函数运行WebSocket监听
async def main():
    await listen_to_messages()

# 启动机器人
if __name__ == "__main__":
    asyncio.run(main())
