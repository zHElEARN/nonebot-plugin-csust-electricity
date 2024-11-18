import json

from pathlib import Path
from nonebot import get_plugin_config

from .config import Config


class DataManager:
    def __init__(self, data_storage_path: str) -> None:
        self.data_storage_path = Path(data_storage_path)
        self.data_storage_path.mkdir(parents=True, exist_ok=True)

        self.binding_data = self.load_json("binding_data.json")
        self.scheduled_tasks = self.load_json("scheduled_tasks.json")
        self.query_limit_data = self.load_json("query_limit_data.json")
        self.electricity_data = self.load_json("electricity_data.json")

    def load_json(self, filename: str) -> dict:
        file_path = self.data_storage_path / filename
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json(self, data: dict, filename: str) -> None:
        file_path = self.data_storage_path / filename
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_binding_data(self) -> None:
        temp = self.load_json("binding_data.json")
        self.binding_data = {"group": {}, "user": {}} if temp == {} else temp

    def save_binding_data(self) -> None:
        self.save_json(self.binding_data, "binding_data.json")

    def load_scheduled_tasks(self) -> None:
        temp = self.load_json("scheduled_tasks.json")
        self.scheduled_tasks = {"group": {}, "user": {}} if temp == {} else temp

    def save_scheduled_tasks(self) -> None:
        self.save_json(self.scheduled_tasks, "scheduled_tasks.json")

    def load_query_limit_data(self) -> None:
        temp = self.load_json("query_limit_data.json")
        self.query_limit_data = {"group": {}, "user": {}} if temp == {} else temp

    def save_query_limit_data(self) -> None:
        self.save_json(self.query_limit_data, "query_limit_data.json")

    def load_electricity_data(self) -> None:
        self.electricity_data = self.load_json("electricity_data.json")

    def save_electricity_data(self) -> None:
        self.save_json(self.electricity_data, "electricity_data.json")


config = get_plugin_config(Config).csust_electricity

data_manager = DataManager(config.data_storage_path)
