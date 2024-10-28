# utils.py

import json
from urllib.parse import urlencode

def dict_to_urlencoded(data):
    return urlencode({"jsondata": json.dumps(data["jsondata"]), "funname": data["funname"], "json": data["json"]})
