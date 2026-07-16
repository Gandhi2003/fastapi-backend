"""Authentication & authorization dependencies (the DI heart of security).

`get_current_user` runs on every protected route:
  decode JWT → check Redis denylist → load user → build the CurrentUser principal.

`require_permissions(...)` is a dependency *factory*: routes declare what they
need (`Depends(require_permissions("customers:create"))`) and FastAPI enforces
it before the handler runs. Wiring services here (not in handlers) keeps routes
thin and makes every dependency individually overridable in tests.
"""

from __future__ import annotations

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import db_session
from app.common.enums import parse_permission_code
from app.core.exceptions import AuthenticationError, PermissionDeniedError, TokenRevokedError
from app.core.redis import get_redis
from app.core.security import decode_token
from app.modules.auth.schemas import CurrentUser
from app.modules.auth.service import AuthService
from app.modules.auth.token_service import TokenService
from app.modules.users.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


# --- service factories (composition root for the request) ------------------ #
def get_user_repository(session: AsyncSession = Depends(db_session)) -> UserRepository:
    return UserRepository(session)


def get_token_service(
    session: AsyncSession = Depends(db_session),
    redis: Redis = Depends(get_redis),
) -> TokenService:
    return TokenService(session, redis)


def get_auth_service(
    users: UserRepository = Depends(get_user_repository),
    tokens: TokenService = Depends(get_token_service),
) -> AuthService:
    return AuthService(users, tokens)


# --- current user ---------------------------------------------------------- #
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    users: UserRepository = Depends(get_user_repository),
    tokens: TokenService = Depends(get_token_service),
) -> CurrentUser:
    if credentials is None:
        raise AuthenticationError("Missing bearer token.")

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc

    if await tokens.is_denylisted(payload["jti"]):
        raise TokenRevokedError()

    # JWT "sub" is a string; user ids are now integers.
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Invalid token subject.") from exc

    user = await users.get_with_roles(user_id)
    if user is None or user.is_deleted:
        raise AuthenticationError("User no longer exists.")

    request.state.user_id = str(user.id)  # for audit/logging
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superuser=user.is_superuser,
        permissions=user.permission_codes,
    )


# --- permission enforcement (RBAC + permission-based) ---------------------- #
def require_permissions(*required: str) -> object:
    """Dependency factory enforcing that the caller holds ALL given permissions.

    Routes declare permissions with readable strings (``"customers:create"``);
    those are converted to their integer codes here to compare against the user's
    stored integer permission codes.
    """
    required_codes = {parse_permission_code(code): code for code in required}

    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.is_superuser:
            return user
        missing = {name for code, name in required_codes.items() if code not in user.permissions}
        if missing:
            raise PermissionDeniedError(
                f"Missing required permission(s): {', '.join(sorted(missing))}"
            )
        return user

    return Depends(_checker)
