# utils.py

import json
from urllib.parse import urlencode

def dict_to_urlencoded(data):
    return urlencode({"jsondata": json.dumps(data["jsondata"]), "funname": data["funname"], "json": data["json"]})

def get_aid(area):
    """根据校区名称选择 aid，若未知校区则报错"""
    aid_map = {
        "云塘": "0030000000002501",
        "金盆岭": "0030000000002502"
    }
    if area not in aid_map:
        raise ValueError(f"未知校区：{area}。仅支持 '云塘' 和 '金盆岭' 校区")
    return aid_map[area]
