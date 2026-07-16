"""Product entity — catalog items, optionally grouped into a Category."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IntPkMixin, SoftDeleteMixin, TimestampMixin


class Product(Base, IntPkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)  # kg, litre, bag…
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
