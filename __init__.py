from .data_manager import data_manager
from .config import Config
from .commands.scheduler import *
from .commands.bind import *
from .commands.electricity import *
from .commands.help import *
from .commands.test import *

import nonebot
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from pathlib import Path


__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-csust-electricity",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config).csust_electricity

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)


data_manager.load_query_limit_data()
