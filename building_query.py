# building_query.py

import requests
import json
from config import QUERY_URL, QUERY_HEADERS
from utils import dict_to_urlencoded

building_query_params = {
    "jsondata": {
        "query_elec_building": {
            "aid": "0030000000002501",
            "account": "317064",
            "area": { "area": "云塘校区", "areaname": "云塘校区" }
        }
    },
    "funname": "synjones.onecard.query.elec.building",
    "json": "true"
}

def query_buildings():
    """查询所有宿舍楼栋信息，返回名称与 buildingid"""
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
