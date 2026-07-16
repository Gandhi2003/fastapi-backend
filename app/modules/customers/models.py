"""Customer entity — the reference template every domain module follows.

A module is a self-contained vertical slice:
    models.py → schemas.py → repository.py → service.py → router.py
This co-location (vs. layer-first folders) is what keeps 100+ modules navigable:
everything about "customers" lives in one folder.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IntPkMixin, SoftDeleteMixin, TimestampMixin


class Customer(Base, IntPkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO-3166

    # Ownership / multi-tenancy hook — index supports per-owner list queries.
    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
