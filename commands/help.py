from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event
from nonebot.rule import to_me

help_command = on_command("电量帮助", aliases={"帮助"}, rule=to_me())


@help_command.handle()
async def handle_help(event: Event):
    help_text = """
使用帮助

基本指令：
1. 绑定宿舍：
   命令：绑定 [校区] [宿舍楼] [宿舍号]
   例如：绑定 云塘 1栋 101

2. 解绑宿舍：
   命令：解绑

3. 查询电量：
   - 查询绑定的宿舍电量：电量
   - 查询特定宿舍电量：电量 [校区] [宿舍楼] [宿舍号]
     例如：电量 云塘 1栋 101
   - 查询校区内所有宿舍楼：电量 [校区]
     例如：电量 云塘

4. 统计图表：
   命令：图表
   说明：显示绑定宿舍的电量变化趋势图，预测电量耗尽时间

5. 定时查询：
   命令：定时查询 [时间]
   例如：定时查询 08:00
   说明：每天在指定时间自动查询并通知电量状态

6. 取消定时查询：
   命令：取消定时查询

可用校区：云塘、金盆岭

使用注意：
- 在群聊中使用需要@机器人
- 绑定后一般只需要直接发送"电量"即可查询
- 查看电量趋势和预测，请使用"图表"命令
""".strip()

    await help_command.finish(help_text)
