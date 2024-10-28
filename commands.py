# commands.py

from bindings import load_bindings, save_bindings
from electricity_query import query_electricity

bindings = load_bindings()

def handle_df_command(group_id):
    room_id = bindings.get(str(group_id))
    if room_id:
        return query_electricity(room_id)
    else:
        return "尚未绑定宿舍，请先使用 .bd 命令绑定宿舍"

def handle_bd_command(group_id, room_id):
    bindings[str(group_id)] = room_id
    save_bindings(bindings)
    return f"宿舍 {room_id} 绑定成功！"
