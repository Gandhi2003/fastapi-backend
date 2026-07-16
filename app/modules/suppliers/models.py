"""Supplier entity — inbound vendors / input suppliers."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IntPkMixin, SoftDeleteMixin, TimestampMixin


class Supplier(Base, IntPkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    company: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO-3166

    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
