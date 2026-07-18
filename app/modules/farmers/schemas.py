from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FarmerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    village: str | None = Field(default=None, max_length=150)
    district: str | None = Field(default=None, max_length=150)
    state: str | None = Field(default=None, max_length=150)
    land_size_acres: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    primary_crop: str | None = Field(default=None, max_length=120)


class FarmerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    village: str | None = Field(default=None, max_length=150)
    district: str | None = Field(default=None, max_length=150)
    state: str | None = Field(default=None, max_length=150)
    land_size_acres: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    primary_crop: str | None = Field(default=None, max_length=120)


class FarmerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None
    email: EmailStr | None
    village: str | None
    district: str | None
    state: str | None
    land_size_acres: Decimal | None
    primary_crop: str | None
    owner_id: int | None
    created_at: datetime
    updated_at: datetime
