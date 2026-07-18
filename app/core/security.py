from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

TokenType = Literal["access", "refresh"]

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=4,
)


def hash_password(plain: str) -> str:
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_needs_rehash(hashed: str) -> bool:
    return _password_hasher.check_needs_rehash(hashed)


@lru_cache
def _signing_key() -> str:
    if settings.JWT_ALGORITHM.startswith("HS"):
        return settings.SECRET_KEY
    return settings.JWT_PRIVATE_KEY_PATH.read_text()


@lru_cache
def _verifying_key() -> str:
    if settings.JWT_ALGORITHM.startswith("HS"):
        return settings.SECRET_KEY
    return settings.JWT_PUBLIC_KEY_PATH.read_text()


def create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": settings.APP_NAME,
    }
    if extra_claims:
        payload.update(extra_claims)
    encoded = jwt.encode(payload, _signing_key(), algorithm=settings.JWT_ALGORITHM)
    return encoded, jti, expires_at


def create_access_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> tuple[str, str, datetime]:
    return create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims,
    )


def create_refresh_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> tuple[str, str, datetime]:
    return create_token(
        subject,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims,
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = jwt.decode(
        token,
        _verifying_key(),
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.APP_NAME,
        options={"require": ["exp", "iat", "sub", "jti", "type"]},
    )
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(
            f"Expected '{expected_type}' token, got '{payload.get('type')}'"
        )
    return payload
