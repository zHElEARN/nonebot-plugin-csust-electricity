# app.py

import asyncio
import websockets
import json
import logging
from config import WS_URL
from message_handler import handle_message

# 日志配置
logging.basicConfig(
    level=logging.INFO,  # 设定日志级别
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),  # 输出到文件
        logging.StreamHandler(),  # 输出到控制台
    ],
)

logger = logging.getLogger(__name__)


async def listen_to_messages():
    logger.info("启动 WebSocket 连接...")
    async with websockets.connect(WS_URL) as websocket:
        logger.info("WebSocket连接已建立，开始监听消息...")

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            logger.debug(f"收到消息: {data}")
            await handle_message(data)


if __name__ == "__main__":
    asyncio.run(listen_to_messages())
