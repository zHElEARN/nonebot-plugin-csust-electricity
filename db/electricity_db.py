import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Binding(Base):
    __tablename__ = "bindings"

    id: str = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键UUID",
    )
    qq_number: Optional[str] = Column(String(20), nullable=True, comment="QQ号")
    group_number: Optional[str] = Column(String(20), nullable=True, comment="群号")
    campus = Column(String(50), nullable=False, comment="校区名称")
    building = Column(String(50), nullable=False, comment="楼栋名称")
    room = Column(String(20), nullable=False, comment="房间号")

    __table_args__ = (
        CheckConstraint(
            "qq_number IS NOT NULL OR group_number IS NOT NULL",
            name="check_contact_exists",
        ),
        CheckConstraint(
            "(qq_number IS NULL AND group_number IS NOT NULL) OR "
            "(qq_number IS NOT NULL AND group_number IS NULL)",
            name="check_single_contact",
        ),
        UniqueConstraint("qq_number", name="uq_qq"),
        UniqueConstraint("group_number", name="uq_group"),
    )


class Schedule(Base):
    __tablename__ = "schedules"

    id: str = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键UUID",
    )
    contact: str = Column(String(20), nullable=False, index=True, comment="QQ号或群号")
    contact_type: str = Column(
        Enum("qq", "group", name="contact_type"), nullable=False, comment="联系类型"
    )
    schedule_time: str = Column(String(5), nullable=False, comment="定时时间(HH:mm)")


class ElectricityHistory(Base):
    __tablename__ = "electricity_history"

    id: str = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键UUID",
    )
    record_time: datetime = Column(DateTime, default=datetime.now, comment="记录时间")
    electricity: float = Column(Float, nullable=False, comment="电量值")
    campus = Column(String(50), nullable=False, comment="校区名称")
    building = Column(String(50), nullable=False, comment="楼栋名称")
    room = Column(String(20), nullable=False, comment="房间号")


SQLALCHEMY_DATABASE_URL = "sqlite:///./electricity.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
