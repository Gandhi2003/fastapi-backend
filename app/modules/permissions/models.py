"""Permission entity — the atom of authorization.

A permission is a stable string like ``customers:create`` or ``orders:refund``.
Endpoints require a permission; roles bundle permissions; users hold roles. This
indirection means access policy changes are data changes (assign/revoke), not
code deploys — essential at 100+ modules.
"""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ActionType, ResourceType
from app.db.base import Base
from app.db.mixins import IntPkMixin, TimestampMixin
from app.db.types import IntEnumType


class Permission(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "permissions"

    # Integer code = resource*10 + action, e.g. customers:read -> 42. Derived, unique.
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    # Human-readable label shown in UIs, e.g. "Read customers".
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Stored as SMALLINT (1, 2, 3, …); only valid enum members are accepted.
    resource: Mapped[ResourceType] = mapped_column(
        IntEnumType(ResourceType), index=True, nullable=False
    )
    action: Mapped[ActionType] = mapped_column(IntEnumType(ActionType), nullable=False)
