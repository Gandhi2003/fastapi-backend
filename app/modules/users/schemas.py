from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.common.enums import UserStatus


class RoleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=12, max_length=128)
    is_superuser: bool = False
    status: UserStatus = UserStatus.ACTIVE
    role_ids: list[int] = Field(default_factory=list)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isalnum():
            raise ValueError("Password must contain a non-alphanumeric character.")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    password: str | None = Field(default=None, min_length=12, max_length=128)
    is_superuser: bool | None = None
    status: UserStatus | None = None
    role_ids: list[int] | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is not None and v.isalnum():
            raise ValueError("Password must contain a non-alphanumeric character.")
        return v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    status: UserStatus
    is_superuser: bool
    mfa_enabled: bool
    last_login_at: datetime | None
    roles: list[RoleSummary] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
