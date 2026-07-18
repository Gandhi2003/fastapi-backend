"""Auth HTTP endpoints. Thin controllers: validate → call service → wrap result.

No business logic lives here. Each route declares its dependencies (services,
current user, permissions); FastAPI resolves them. Responses use the standard
envelope for consistency with the rest of the API.
"""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_auth_service, get_current_user, get_token_service
from app.common.schemas.response import ResponseEnvelope, ok
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.modules.auth import mfa_service
from app.modules.auth.schemas import (
    CurrentUser,
    LoginRequest,
    MFASetupResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.modules.auth.service import AuthService
from app.modules.auth.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[dict[str, str]]:
    user = await service.register(payload)
    return ok({"id": str(user.id), "email": user.email, "status": user.status})


@router.post("/login")
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[TokenPair]:
    pair = await service.authenticate(payload)
    return ok(pair)


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    tokens: TokenService = Depends(get_token_service),
    service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[TokenPair]:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid refresh token.") from exc

    user = await service.users.get_with_roles(claims["sub"])
    if user is None:
        raise AuthenticationError("User no longer exists.")

    pair = await tokens.rotate(claims["jti"], user.id, user.permission_codes)
    return ok(pair)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    tokens: TokenService = Depends(get_token_service),
    _: CurrentUser = Depends(get_current_user),
) -> ResponseEnvelope[dict[str, str]]:
    # Denylist the presented access token immediately.
    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    claims = decode_token(token, expected_type="access")
    from datetime import UTC, datetime

    await tokens.revoke_access_jti(claims["jti"], datetime.fromtimestamp(claims["exp"], tz=UTC))
    return ok({"detail": "Logged out."})


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)) -> ResponseEnvelope[CurrentUser]:
    return ok(user)


# --- MFA ------------------------------------------------------------------- #
@router.post("/mfa/setup")
async def mfa_setup(
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[MFASetupResponse]:
    secret = mfa_service.generate_secret()
    db_user = await service.users.get(user.id)
    assert db_user is not None
    await service.users.update(db_user, mfa_secret=secret)  # confirmed on verify
    await service.session.commit()
    uri = mfa_service.provisioning_uri(secret, user.email)
    return ok(MFASetupResponse(secret=secret, otpauth_uri=uri))
