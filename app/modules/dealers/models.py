"""Dealer entity — distribution partners."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IntPkMixin, SoftDeleteMixin, TimestampMixin


class Dealer(Base, IntPkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "dealers"

    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    company: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    region: Mapped[str | None] = mapped_column(String(150), index=True, nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
