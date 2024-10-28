# electricity_query.py

import requests
import json
from datetime import datetime
from config import QUERY_URL, QUERY_HEADERS
from utils import dict_to_urlencoded

query_params_template = {
    "jsondata": {
        "query_elec_roominfo": {
            "aid": "0030000000002501",
            "account": "317064",
            "room": {"roomid": "", "room": ""},
            "floor": {"floorid": "", "floor": ""},
            "area": {"area": "云塘校区", "areaname": "云塘校区"},
            "building": {"buildingid": "557", "building": "至诚轩5栋A区"}
        }
    },
    "funname": "synjones.onecard.query.elec.roominfo",
    "json": "true"
}

def query_electricity(room_id):
    try:
        query_params = query_params_template.copy()
        query_params["jsondata"]["query_elec_roominfo"]["room"]["roomid"] = room_id
        query_params["jsondata"]["query_elec_roominfo"]["room"]["room"] = room_id

        encoded_data = dict_to_urlencoded(query_params)
        response = requests.post(QUERY_URL, headers=QUERY_HEADERS, data=encoded_data)
        response.raise_for_status()

        result = response.json()
        info = result.get("query_elec_roominfo", {})

        room = info.get("room", {}).get("room", "未知宿舍")
        electricity = info.get("errmsg", "未知电量")
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"查询时间：{query_time}\n宿舍：{room}\n剩余电量：{electricity}"

    except (requests.exceptions.RequestException, json.JSONDecodeError):
        return "查询失败，网络请求错误"
