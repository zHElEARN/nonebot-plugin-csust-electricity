from pathlib import Path
import subprocess

import nonebot
from nonebot import get_plugin_config, on_command, logger
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="nonebot-cupsprint",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)

GROUP_WHITELIST = [713154536, 966613029]

print_command = on_command("打印", rule=to_me())

async def download_file(url: str, filename: str) -> str:
    """
    使用 curl 从指定 URL 下载文件，并保存为 filename。
    返回下载后的文件路径。
    """
    file_path = f"/tmp/{filename}"
    try:
        # 使用 curl 下载文件并禁用 SSL 验证（可以根据需求去掉 --insecure）
        subprocess.run(
            ["curl", "-L", "--insecure", "-o", file_path, url],
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info(f"文件下载成功: {file_path}")
        return file_path
    except subprocess.CalledProcessError as e:
        logger.error(f"文件下载失败: {e.stderr}")
        return None

@print_command.handle()
async def handle_print(event: Event):
    if isinstance(event, GroupMessageEvent):
        if not event.group_id in GROUP_WHITELIST:
            return

        # 检查消息是否为回复消息
        if event.reply:
            msg = event.reply.message

            for segment in msg:
                # 处理图片消息
                if segment.type == "image":
                    url = segment.data["url"]
                    logger.info(f"Image URL: {url}")
                    
                    # 下载图片
                    file_path = await download_file(url, "image_to_print.jpg")
                    if file_path:
                        # 使用 lp 命令打印文件
                        subprocess.run(["lp", file_path], check=True)
                        await print_command.finish("图片已成功打印。")

                # 处理文件消息
                elif segment.type == "file":
                    res = await nonebot.get_bot().call_api("get_group_file_url", file_id=segment.data["file_id"], group_id=event.group_id)
                    url = res["url"]
                    name = segment.data["file"]

                    logger.info(f"File URL: {url}")
                    logger.info(f"File Name: {name}")
                    
                    # 下载文件
                    file_path = await download_file(url, name)
                    if file_path:
                        # 使用 lp 命令打印文件
                        subprocess.run(["lp", file_path], check=True)
                        await print_command.finish(f"文件 {name} 已成功打印。")

                else:
                    await print_command.finish("未检测到可打印的文件或图片。")
