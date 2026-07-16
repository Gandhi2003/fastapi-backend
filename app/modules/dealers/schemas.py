"""Dealer DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DealerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    region: str | None = Field(default=None, max_length=150)
    gst_number: str | None = Field(default=None, max_length=20)


class DealerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    region: str | None = Field(default=None, max_length=150)
    gst_number: str | None = Field(default=None, max_length=20)


class DealerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str | None
    email: EmailStr | None
    phone: str | None
    region: str | None
    gst_number: str | None
    owner_id: int | None
    created_at: datetime
    updated_at: datetime
