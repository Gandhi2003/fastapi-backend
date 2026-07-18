from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isalnum():
            raise ValueError("Password must contain a non-alphanumeric character.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = Field(default=None, description="6-digit TOTP, if MFA enabled.")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access-token lifetime in seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_uri: str  # render as a QR code client-side


class MFAVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class CurrentUser(BaseModel):
    """The authenticated principal attached to a request."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_superuser: bool
    permissions: set[int] = Field(default_factory=set)  # integer permission codes


class SessionInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    last_seen_at: datetime | None
    trusted: bool
