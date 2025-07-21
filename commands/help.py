from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event
from nonebot.rule import to_me

help_command = on_command("电量帮助", aliases={"帮助"}, rule=to_me())


@help_command.handle()
async def handle_help(event: Event):
    help_text = """
使用帮助

先查看校区的所有宿舍楼名称，使用“/电量 金盆岭”或者“/电量 云塘”查看
然后可以使用“/电量 [校区] [宿舍楼] [宿舍号]”直接查询特定宿舍的电量
对于云塘校区宿舍有A、B区之分，宿舍号需要加大写的前缀，如“A233”
如果需要绑定宿舍，可以使用“/绑定 [校区] [宿舍楼] [宿舍号]”进行绑定
解绑宿舍使用“/解绑”命令
绑定后可使用“/电量”命令直接查询绑定宿舍的电量
绑定后可使用“/图表”命令查看电量变化趋势和预测电量耗尽时间
绑定后可使用“/定时查询 [时间]”命令设置每天定时查询电量状态
如果需要取消定时查询，使用“/取消定时查询”命令
如果需要清除历史记录，使用“/清除历史”命令
""".strip()

    await help_command.finish(help_text)
