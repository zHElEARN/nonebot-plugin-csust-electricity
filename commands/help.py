from nonebot import on_command, require
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageSegment

require("nonebot_plugin_txt2img")
from nonebot_plugin_txt2img import Txt2Img


help_command = on_command("帮助", aliases={"help"}, rule=to_me())


@help_command.handle()
async def handle_help():
    help_text = """
机器人使用帮助：
1.  查询电量：
    发送“/电量 校区 宿舍楼 宿舍号”来查询电量
    可以通过输入“/电量 校区”来查看对应校区的宿舍楼
    例如：/电量 云塘 至诚轩5栋A区 A233
    
2.  绑定宿舍：
    发送“/绑定宿舍 校区 宿舍楼 宿舍号”来绑定宿舍
    例如：/绑定宿舍 云塘 16栋A区 A101
    （绑定之后可以直接发送“/电量”进行查询）
    
3.  解绑宿舍：
    在群聊中和私聊中均可发送“/解绑”来解绑宿舍
    
4.  定时查询：
    发送“/定时查询 HH:MM”来设置定时查询
    例如：/定时查询 08:00
    
5.  取消定时查询：
    在群聊中和私聊中均可发送“/取消定时查询”来取消定时提醒

6. 图表功能：
    发送“/图表”来查看电量变化图表
    （需要先绑定宿舍）
"""

    # 创建图片
    pic = Txt2Img().draw("机器人帮助", help_text)

    # 发送图片消息
    await help_command.send(MessageSegment.image(pic))
