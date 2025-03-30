import json
import re
from dataclasses import dataclass
from typing import Dict, List

import requests
from nonebot import logger


@dataclass
class Campus:
    name: str
    id: str
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = f"{self.name}校区"


@dataclass
class Building:
    name: str
    id: str
    campus: Campus


@dataclass
class Room:
    id: str
    building: Building


@dataclass
class ElectricityInfo:
    value: float
    room: Room
    raw_message: str = ""

proxies = {
    "http": None,
    "https": None,
}


class CSUSTElectricityAPI:
    QUERY_URL = "http://yktwd.csust.edu.cn:8988/web/Common/Tsm.html"
    HEADERS = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    CAMPUS_MAP = {"云塘": "0030000000002501", "金盆岭": "0030000000002502"}

    def __init__(self):
        self.campuses: Dict[str, Campus] = {
            name: Campus(name=name, id=campus_id)
            for name, campus_id in self.CAMPUS_MAP.items()
        }
        self.buildings_cache: Dict[str, Dict[str, Building]] = {}

    def get_campuses(self) -> List[Campus]:
        return list(self.campuses.values())

    def get_campus_names(self) -> List[str]:
        return list(self.campuses.keys())

    def get_buildings(self, campus_name: str) -> Dict[str, Building]:
        if campus_name not in self.campuses:
            raise ValueError(
                f"无效的校区名称: {campus_name}，可用校区: {', '.join(self.get_campus_names())}"
            )

        campus = self.campuses[campus_name]

        if campus_name in self.buildings_cache:
            return self.buildings_cache[campus_name]

        data = {
            "jsondata": {
                "query_elec_building": {
                    "aid": campus.id,
                    "account": "000001",
                    "area": {
                        "area": campus.display_name,
                        "areaname": campus.display_name,
                    },
                }
            },
            "funname": "synjones.onecard.query.elec.building",
            "json": "true",
        }

        try:
            response = requests.post(
                self.QUERY_URL,
                headers=self.HEADERS,
                data={
                    "jsondata": json.dumps(data["jsondata"]),
                    "funname": data["funname"],
                    "json": data["json"],
                },
                proxies=proxies
            )
            response.raise_for_status()
            result = response.json()

            if "query_elec_building" not in result:
                raise ValueError(f"API返回数据格式错误: {result}")

            building_info = result.get("query_elec_building", {}).get("buildingtab", [])

            building_dict = {}
            for item in building_info:
                building = Building(
                    name=item["building"], id=item["buildingid"], campus=campus
                )
                building_dict[building.name] = building

            if not building_dict:
                raise ValueError(f"未能获取到{campus_name}校区的楼栋信息")

            sorted_buildings = {
                k: v
                for k, v in sorted(
                    building_dict.items(), key=lambda item: int(item[1].id)
                )
            }

            self.buildings_cache[campus_name] = sorted_buildings
            logger.info(
                f"成功获取到{campus_name}校区的楼栋信息，共 {len(sorted_buildings)} 个楼栋"
            )
            return sorted_buildings

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"连接服务器失败: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"解析服务器响应失败: {e}")

    def get_all_buildings(self) -> Dict[str, Dict[str, Building]]:
        result = {}
        for campus_name in self.campuses:
            result[campus_name] = self.get_buildings(campus_name)
        return result

    def get_electricity(
        self, campus_name: str, building_name: str, room_id: str
    ) -> ElectricityInfo:
        if campus_name not in self.campuses:
            raise ValueError(
                f"无效的校区名称: {campus_name}，可用校区: {', '.join(self.get_campus_names())}"
            )

        campus = self.campuses[campus_name]

        buildings = self.get_buildings(campus_name)

        if building_name not in buildings:
            raise ValueError(
                f"无效的楼栋名称: {building_name}，可用楼栋: {', '.join(buildings.keys())}"
            )

        building = buildings[building_name]

        if not room_id or not isinstance(room_id, str):
            raise ValueError("房间号不能为空且必须是字符串")

        room = Room(id=room_id, building=building)

        query_params = {
            "jsondata": {
                "query_elec_roominfo": {
                    "aid": campus.id,
                    "account": "000001",
                    "room": {"roomid": room_id, "room": room_id},
                    "floor": {"floorid": "", "floor": ""},
                    "area": {
                        "area": campus.display_name,
                        "areaname": campus.display_name,
                    },
                    "building": {"buildingid": building.id, "building": ""},
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
            response = requests.post(
                self.QUERY_URL, headers=self.HEADERS, data=encoded_data, proxies=proxies
            )
            response.raise_for_status()

            result = response.json()

            if "query_elec_roominfo" not in result:
                raise ValueError(f"API返回数据格式错误: {result}")

            info = result.get("query_elec_roominfo", {})

            if "error" in info and info["error"] != "0":
                error_msg = info.get("errmsg", "未知错误")
                raise ValueError(f"查询失败: {error_msg}")

            electricity_msg: str = info.get("errmsg", "")

            if not electricity_msg:
                raise ValueError("未返回电量信息")

            match = re.search(r"(\d+(\.\d+)?)", electricity_msg)
            if not match:
                raise ValueError(f"无法从返回结果中解析电量数值: {electricity_msg}")

            electricity_value = float(match.group())

            return ElectricityInfo(
                value=electricity_value, room=room, raw_message=electricity_msg
            )

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"连接服务器失败: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"解析服务器响应失败: {e}")


csust_api = CSUSTElectricityAPI()


if __name__ == "__main__":
    api = CSUSTElectricityAPI()

    campuses = api.get_campuses()
    logger.info(f"可用校区: {[campus.name for campus in campuses]}")

    for campus in campuses:
        buildings = api.get_buildings(campus.name)
        logger.info(f"{campus.name}校区楼栋: {list(buildings.keys())}")

    try:
        info = api.get_electricity("云塘", "至诚轩5栋A区", "A544")
        logger.info(f"房间 {info.room.id} 电量: {info.value} 度")
        logger.info(f"原始消息: {info.raw_message}")
    except Exception as e:
        logger.error(f"查询失败: {e}")
