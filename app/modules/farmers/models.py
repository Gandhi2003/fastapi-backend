"""Farmer entity — agricultural partner profiles."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IntPkMixin, SoftDeleteMixin, TimestampMixin


class Farmer(Base, IntPkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "farmers"

    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    village: Mapped[str | None] = mapped_column(String(150), nullable=True)
    district: Mapped[str | None] = mapped_column(String(150), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(150), nullable=True)
    land_size_acres: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    primary_crop: Mapped[str | None] = mapped_column(String(120), nullable=True)

    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
