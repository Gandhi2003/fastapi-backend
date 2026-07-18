"""Auth service — orchestrates the authentication use-cases.

This is the Service Layer: it contains business rules and coordinates
repositories, the token service, hashing, MFA and side-effects (emails via
Celery). It depends only on abstractions (repositories, services) and raises
domain exceptions — it never touches FastAPI request/response objects.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.common.enums import AuthProvider, UserStatus
from app.core.config import settings
from app.core.exceptions import (
    AccountLockedError,
    ConflictError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    MFARequiredError,
)
from app.core.logging import get_logger
from app.core.security import hash_password, password_needs_rehash, verify_password
from app.modules.auth import mfa_service
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenPair
from app.modules.auth.token_service import TokenService
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

logger = get_logger(__name__)


class AuthService:
    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self.users = users
        self.tokens = tokens
        self.session = users.session

    async def register(self, payload: RegisterRequest) -> User:
        if await self.users.get_by_email(payload.email):
            raise ConflictError("An account with this email already exists.")

        user = await self.users.create(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            auth_provider=AuthProvider.LOCAL,
            status=UserStatus.PENDING,
        )
        await self.session.commit()
        await self.session.refresh(user)
        logger.info("user_registered", user_id=str(user.id))
        return user

    async def authenticate(self, payload: LoginRequest) -> TokenPair:
        user = await self.users.get_by_email(payload.email)

        if user is None or user.hashed_password is None:
            verify_password(payload.password, _DUMMY_HASH)
            raise InvalidCredentialsError()

        self._assert_not_locked(user)

        if not verify_password(payload.password, user.hashed_password):
            await self._register_failed_attempt(user)
            raise InvalidCredentialsError()

        if user.status == UserStatus.PENDING or not user.is_email_verified:
            raise EmailNotVerifiedError()
        if user.status == UserStatus.SUSPENDED:
            raise InvalidCredentialsError("Account is suspended.")

        if user.mfa_enabled:
            if not payload.mfa_code:
                raise MFARequiredError()
            if not mfa_service.verify_code(user.mfa_secret or "", payload.mfa_code):
                await self._register_failed_attempt(user)
                raise InvalidCredentialsError("Invalid MFA code.")

        await self._on_successful_login(user)

        if password_needs_rehash(user.hashed_password):
            await self.users.update(user, hashed_password=hash_password(payload.password))
            await self.session.commit()

        return await self.tokens.issue_pair(user.id, user.permission_codes)

    def _assert_not_locked(self, user: User) -> None:
        if user.locked_until and user.locked_until > datetime.now(UTC):
            raise AccountLockedError()

    async def _register_failed_attempt(self, user: User) -> None:
        attempts = user.failed_login_attempts + 1
        updates: dict[str, Any] = {"failed_login_attempts": attempts}
        if attempts >= settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
            updates["locked_until"] = datetime.now(UTC) + timedelta(
                minutes=settings.ACCOUNT_LOCKOUT_DURATION_MINUTES
            )
            logger.warning("account_locked", user_id=str(user.id))
        await self.users.update(user, **updates)
        await self.session.commit()

    async def _on_successful_login(self, user: User) -> None:
        await self.users.update(
            user,
            failed_login_attempts=0,
            locked_until=None,
            last_login_at=datetime.now(UTC),
        )
        await self.session.commit()


# Pre-computed dummy Argon2 hash used to equalize timing for unknown users.
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalization")
