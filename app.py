# app.py

import asyncio
import websockets
import json
from config import WS_URL
from message_handler import handle_message

async def listen_to_messages():
    async with websockets.connect(WS_URL) as websocket:
        print("WebSocket连接已建立，开始监听消息...")

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            await handle_message(data)

if __name__ == "__main__":
    asyncio.run(listen_to_messages())
