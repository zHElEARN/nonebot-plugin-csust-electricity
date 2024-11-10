import re
import requests
import json

from nonebot import logger

# 配置
QUERY_URL = "http://yktwd.csust.edu.cn:8988/web/Common/Tsm.html"
HEADERS = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

# 校区和楼栋的映射
CAMPUS_IDS = {"云塘": "0030000000002501", "金盆岭": "0030000000002502"}


def get_buildings_for_campus(campus_name, aid):
    """查询指定校区的所有楼栋信息"""
    data = {
        "jsondata": {
            "query_elec_building": {
                "aid": aid,
                "account": "000001",
                "area": {
                    "area": campus_name + "校区",
                    "areaname": campus_name + "校区",
                },
            }
        },
        "funname": "synjones.onecard.query.elec.building",
        "json": "true",
    }

    try:
        response = requests.post(
            QUERY_URL,
            headers=HEADERS,
            data={
                "jsondata": json.dumps(data["jsondata"]),
                "funname": data["funname"],
                "json": data["json"],
            },
        )
        response.raise_for_status()
        result = response.json()

        building_info = result.get("query_elec_building", {}).get("buildingtab", [])
        buildings = {item["building"]: item["buildingid"] for item in building_info}

        logger.info(
            f"成功获取到{campus_name}校区的楼栋信息，共 {len(buildings)} 个楼栋。"
        )
        return dict(sorted(buildings.items(), key=lambda item: int(item[1])))
    except requests.exceptions.RequestException as e:
        logger.error(f"{campus_name}校区的楼栋查询失败: {e}")
        return {}


def fetch_building_data():
    """爬取并保存所有校区楼栋信息"""
    all_buildings = {}

    for campus_name, aid in CAMPUS_IDS.items():
        buildings = get_buildings_for_campus(campus_name, aid)
        all_buildings[campus_name] = buildings
        # time.sleep(1)  # 控制请求频率

    return all_buildings


def fetch_electricity_data(campus, building_id, room_id):
    """获取指定校区、楼栋、宿舍的电量信息"""
    aid = CAMPUS_IDS.get(campus)
    if not aid:
        raise ValueError(f"未知校区: {campus}")

    query_params = {
        "jsondata": {
            "query_elec_roominfo": {
                "aid": aid,
                "account": "000001",
                "room": {"roomid": room_id, "room": room_id},
                "floor": {"floorid": "", "floor": ""},
                "area": {"area": f"{campus}校区", "areaname": f"{campus}校区"},
                "building": {"buildingid": building_id, "building": ""},
            }
        },
        "funname": "synjones.onecard.query.elec.roominfo",
        "json": "true",
    }

    try:
        encoded_data = {
            "jsondata": json.dumps(query_params["jsondata"]),
            "funname": query_params["funname"],
            "json": query_params["json"],
        }
        response = requests.post(QUERY_URL, headers=HEADERS, data=encoded_data)
        response.raise_for_status()

        result = response.json()
        info = result.get("query_elec_roominfo", {})

        room = info.get("room", {}).get("room", "未知宿舍")
        electricity = info.get("errmsg", "未知电量")

        match = re.search(r"(\d+(\.\d+)?)", electricity)
        if match:
            electricity_value = match.group()
        else:
            electricity_value = "未知"
        return {
            "宿舍": room,
            "剩余电量": f"{electricity_value} 度",
        }

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logger.info(f"电量查询失败: {e}")
        return {"error": f"查询失败: {e}"}


# 主函数，用于直接运行脚本时调用
if __name__ == "__main__":
    # 示例：查询楼栋信息
    fetch_building_data()

    # 示例：查询宿舍电量
    campus = "云塘"
    building_id = "557"
    room_id = "A544"

    electricity_data = fetch_electricity_data(campus, building_id, room_id)
    print(electricity_data)
