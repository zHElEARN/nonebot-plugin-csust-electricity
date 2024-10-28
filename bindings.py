# bindings.py

import json
from config import BINDINGS_FILE

def load_bindings():
    """加载持久化的群号和宿舍绑定信息"""
    try:
        with open(BINDINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_bindings(bindings):
    """保存群号和宿舍绑定信息到文件"""
    with open(BINDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(bindings, f, ensure_ascii=False, indent=4)
