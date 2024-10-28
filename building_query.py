import json
import requests
from config import QUERY_URL, QUERY_HEADERS
from utils import dict_to_urlencoded, get_aid

def query_buildings(area):
    """查询指定校区的所有宿舍楼栋信息，返回名称与 buildingid"""
    try:
        # 获取 aid
        aid = get_aid(area)

        building_query_params = {
            "jsondata": {
                "query_elec_building": {
                    "aid": aid,
                    "account": "000001",
                    "area": {"area": area + "校区", "areaname": area + "校区"},
                }
            },
            "funname": "synjones.onecard.query.elec.building",
            "json": "true",
        }

        encoded_data = dict_to_urlencoded(building_query_params)
        response = requests.post(QUERY_URL, headers=QUERY_HEADERS, data=encoded_data)
        response.raise_for_status()

        result = response.json()
        building_info = result.get("query_elec_building", {}).get("buildingtab", [])

        buildings = {item["building"]: item["buildingid"] for item in building_info}
        return dict(sorted(buildings.items(), key=lambda item: int(item[1]))) if buildings else "没有获取到楼栋信息。"
    
    except ValueError as e:
        return str(e)
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        return f"查询失败: {e}"
