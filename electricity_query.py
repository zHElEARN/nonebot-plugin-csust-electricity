import re
import requests
import json
import logging
from datetime import datetime
from config import QUERY_URL, QUERY_HEADERS
from utils import dict_to_urlencoded, get_aid

logger = logging.getLogger(__name__)

query_params_template = {
    "jsondata": {
        "query_elec_roominfo": {
            "aid": "",
            "account": "000001",
            "room": {"roomid": "", "room": ""},
            "floor": {"floorid": "", "floor": ""},
            "area": {"area": "", "areaname": ""},
            "building": {"buildingid": "", "building": ""},
        }
    },
    "funname": "synjones.onecard.query.elec.roominfo",
    "json": "true",
}


def query_electricity(area, building_id, room_id):
    """查询电费信息，使用 buildingid 和宿舍号"""
    try:
        aid = get_aid(area)
        logger.info(
            f"查询电费信息: 校区={area}, aid={aid}, building_id={building_id}, room_id={room_id}"
        )

        query_params = query_params_template.copy()
        query_params["jsondata"]["query_elec_roominfo"]["room"]["roomid"] = room_id
        query_params["jsondata"]["query_elec_roominfo"]["room"]["room"] = room_id
        query_params["jsondata"]["query_elec_roominfo"]["building"][
            "buildingid"
        ] = building_id
        query_params["jsondata"]["query_elec_roominfo"]["area"]["area"] = area + "校区"
        query_params["jsondata"]["query_elec_roominfo"]["aid"] = aid

        encoded_data = dict_to_urlencoded(query_params)
        response = requests.post(QUERY_URL, headers=QUERY_HEADERS, data=encoded_data)
        response.raise_for_status()

        result = response.json()
        info = result.get("query_elec_roominfo", {})

        room = info.get("room", {}).get("room", "未知宿舍")
        electricity_msg = info.get("errmsg", "未知电量")

        match = re.search(r"(\d+(\.\d+)?)", electricity_msg)
        if match:
            electricity_amount = match.group() + "度"
        else:
            electricity_amount = "未知"

        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"电费查询成功: {room} 剩余电量={electricity_amount}")
        return f"查询时间：{query_time}\n宿舍：{room}\n剩余电量：{electricity_amount}"

    except ValueError as e:
        logger.error(f"校区错误: {e}")
        return str(e)
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        logger.error("查询失败，网络请求错误")
        return "查询失败，网络请求错误"
