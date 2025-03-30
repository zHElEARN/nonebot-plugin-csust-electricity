from typing import Literal, Optional, Tuple

from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import FinishedException

from ..csust_api import csust_api
from ..db.electricity_db import Binding, SessionLocal


def get_sender_info(event: Event) -> Tuple[Literal["user", "group"], str]:
    if isinstance(event, PrivateMessageEvent):
        return "user", str(event.get_user_id())
    elif isinstance(event, GroupMessageEvent):
        return "group", str(event.group_id)
    else:
        raise FinishedException("不支持的消息类型")


def get_binding(sender_type: str, id: str) -> Optional[Binding]:
    with SessionLocal() as session:
        if sender_type == "user":
            return session.query(Binding).filter(Binding.qq_number == id).first()
        else:
            return session.query(Binding).filter(Binding.group_number == id).first()


def validate_campus_building(
    campus: str, building: Optional[str] = None
) -> Tuple[bool, str]:
    if campus not in csust_api.get_campus_names():
        return False, "校区名称错误，请检查输入\nTips：校区名称为「金盆岭」或「云塘」"

    if building and building not in csust_api.get_buildings(campus):
        return (
            False,
            "楼栋名称错误，请检查输入\nTips：发送「电量 校区」可以查看校区宿舍楼",
        )

    return True, ""
