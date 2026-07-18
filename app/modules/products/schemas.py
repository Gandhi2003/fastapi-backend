from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, max_length=40)
    price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True
    category_id: int | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, max_length=40)
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    category_id: int | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    description: str | None
    unit: str | None
    price: Decimal
    stock_quantity: int
    is_active: bool
    category_id: int | None
    created_at: datetime
    updated_at: datetime
