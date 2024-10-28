# config.py

# 指令前缀
PREFIX = "."

# 群号白名单
WHITE_LISTED_GROUPS = [966613029, 713154536]

# 电费查询URL与设置
QUERY_URL = "http://yktwd.csust.edu.cn:8988/web/Common/Tsm.html"
QUERY_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

# 群消息发送API
GROUP_MSG_API = "http://192.168.5.5:3000/send_group_msg"

# WebSocket设置
WS_URL = "ws://192.168.5.5:3001"

# 持久化绑定信息文件路径
BINDINGS_FILE = "bindings.json"

# 限速设置
RATE_LIMIT_FILE = "rate_limit.json"  # 持久化限速数据文件
RATE_LIMIT_THRESHOLD = 2             # 每小时查询次数上限
RATE_LIMIT_INTERVAL = 3600           # 限速时间间隔（秒），即1小时
