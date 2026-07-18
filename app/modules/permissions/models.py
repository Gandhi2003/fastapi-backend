from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ActionType, ResourceType
from app.db.base import Base
from app.db.mixins import IntPkMixin, TimestampMixin
from app.db.types import IntEnumType


class Permission(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "permissions"

    code: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource: Mapped[ResourceType] = mapped_column(
        IntEnumType(ResourceType), index=True, nullable=False
    )
    action: Mapped[ActionType] = mapped_column(IntEnumType(ActionType), nullable=False)
