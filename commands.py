# commands.py

from bindings import load_bindings, save_bindings
from electricity_query import query_electricity
from building_query import query_buildings
from rate_limit import check_rate_limit

bindings = load_bindings()

# 定义指令及其描述
COMMANDS = {
    "query": {
        "description": "查询绑定宿舍的电费信息",
        "usage": ".query",
        "example": ".query",
    },
    "bind": {
        "description": "绑定群号和指定楼栋宿舍",
        "usage": ".bind <校区> <楼栋> <寝室>",
        "example": ".bind 云塘 1 A233",
    },
    "buildings": {
        "description": "列出指定区域内的所有宿舍楼信息",
        "usage": ".buildings <校区>",
        "example": ".buildings 云塘",
    },
}

def list_commands():
    """返回可用指令及其说明"""
    command_list = "可用指令："
    for command, info in COMMANDS.items():
        command_list += f"\n\n{info['usage']} - {info['description']} - 例：{info['example']}"
    return command_list

def handle_buildings_command(area):
    """列出所有宿舍楼信息，包括楼栋名称和 buildingid"""
    buildings = query_buildings(area)
    if isinstance(buildings, dict):
        return "可用楼栋列表（楼栋名称 - 楼栋ID）:\n" + "\n".join([f"{name} - {building_id}" for name, building_id in buildings.items()])
    else:
        return buildings  # 返回错误信息

def handle_query_command(group_id):
    """查询绑定宿舍的电费信息，添加限速检查"""
    if not check_rate_limit(group_id):
        return "该群查询频率过高，请稍后再试。每小时最多查询两次。"
    
    room_data = bindings.get(str(group_id))
    if room_data:
        area, building_id, room = room_data["area"], room_data["buildingid"], room_data["room"]
        return query_electricity(area, building_id, room)
    else:
        return "尚未绑定宿舍，请先使用 .bind 命令绑定宿舍"

def handle_bind_command(group_id, area, building_id, room_id):
    """绑定群号和指定楼栋宿舍，包含楼栋名称和 buildingid"""
    bindings[str(group_id)] = {"area": area, "buildingid": building_id, "room": room_id}
    save_bindings(bindings)
    return f"宿舍 {room_id} 绑定成功！"

def handle_invalid_command():
    """处理无效指令的反馈"""
    return "无效指令，请输入 .help 查看可用指令"
