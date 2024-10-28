import requests
import json
from datetime import datetime
from config import QUERY_URL, QUERY_HEADERS
from utils import dict_to_urlencoded, get_aid

query_params_template = {
    "jsondata": {
        "query_elec_roominfo": {
            "aid": "",
            "account": "000001",
            "room": {"roomid": "", "room": ""},
            "floor": {"floorid": "", "floor": ""},
            "area": {"area": "", "areaname": ""},
            "building": {"buildingid": "", "building": ""}
        }
    },
    "funname": "synjones.onecard.query.elec.roominfo",
    "json": "true"
}

def query_electricity(area, building_id, room_id):
    """查询电费信息，使用 buildingid 和宿舍号"""
    try:
        # 获取 aid
        aid = get_aid(area)

        query_params = query_params_template.copy()
        query_params["jsondata"]["query_elec_roominfo"]["room"]["roomid"] = room_id
        query_params["jsondata"]["query_elec_roominfo"]["room"]["room"] = room_id
        query_params["jsondata"]["query_elec_roominfo"]["building"]["buildingid"] = building_id
        query_params["jsondata"]["query_elec_roominfo"]["area"]["area"] = area + "校区"
        query_params["jsondata"]["query_elec_roominfo"]["aid"] = aid

        encoded_data = dict_to_urlencoded(query_params)
        response = requests.post(QUERY_URL, headers=QUERY_HEADERS, data=encoded_data)
        response.raise_for_status()

        result = response.json()
        info = result.get("query_elec_roominfo", {})

        room = info.get("room", {}).get("room", "未知宿舍")
        electricity = info.get("errmsg", "未知电量")
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"查询时间：{query_time}\n宿舍：{room}\n剩余电量：{electricity}"

    except ValueError as e:
        return str(e)
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        return "查询失败，网络请求错误"
