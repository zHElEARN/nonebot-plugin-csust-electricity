# commands.py

from bindings import load_bindings, save_bindings
from electricity_query import query_electricity
from building_query import query_buildings

bindings = load_bindings()

def handle_buildings_command(group_id):
    """列出所有宿舍楼信息，包括楼栋名称和 buildingid"""
    buildings = query_buildings()
    if isinstance(buildings, dict):
        return "可用楼栋列表（楼栋名称 - buildingid）:\n" + "\n".join([f"{name} - {building_id}" for name, building_id in buildings.items()])
    else:
        return buildings  # 返回错误信息

def handle_query_command(group_id):
    """查询绑定宿舍的电费信息"""
    room_data = bindings.get(str(group_id))
    if room_data:
        building_id, room = room_data["buildingid"], room_data["room"]
        return query_electricity(building_id, room)
    else:
        return "尚未绑定宿舍，请先使用 .bd 命令绑定宿舍"

def handle_bind_command(group_id, building_id, room_id):
    """绑定群号和指定楼栋宿舍，包含楼栋名称和 buildingid"""
    bindings[str(group_id)] = {"buildingid": building_id, "room": room_id}
    save_bindings(bindings)
    return f"宿舍 {room_id} 绑定成功！"
