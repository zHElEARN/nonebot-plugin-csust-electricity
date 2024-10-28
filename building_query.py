# building_query.py

import requests
import json
from config import QUERY_URL, QUERY_HEADERS
from utils import dict_to_urlencoded


def query_buildings(area):
    """查询指定校区的所有宿舍楼栋信息，返回名称与 buildingid"""

    # 根据校区选择 aid
    aid = "0030000000002501" if area == "云塘" else "0030000000002502"
    
    building_query_params = {
        "jsondata": {
            "query_elec_building": {
                "aid": aid,
                "account": "317064",
                "area": {"area": area + "校区", "areaname": area + "校区"},
            }
        },
        "funname": "synjones.onecard.query.elec.building",
        "json": "true",
    }

    try:
        encoded_data = dict_to_urlencoded(building_query_params)
        response = requests.post(QUERY_URL, headers=QUERY_HEADERS, data=encoded_data)
        response.raise_for_status()

        result = response.json()
        building_info = result.get("query_elec_building", {}).get("buildingtab", [])

        buildings = {item["building"]: item["buildingid"] for item in building_info}
        if buildings:
            return buildings
        else:
            return "没有获取到楼栋信息。"
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        return f"查询失败: {e}"
