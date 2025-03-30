from pathlib import Path

import nonebot
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .commands.bind import *
from .commands.query import *
from .commands.schedule import *
from .config import Config

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
