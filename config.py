from pydantic import BaseModel


class ScopedConfig(BaseModel):
    data_storage_path: str = "csust-electricity"


class Config(BaseModel):
    csust_electricity: ScopedConfig = ScopedConfig()
