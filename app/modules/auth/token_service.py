from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import TokenRevokedError
from app.core.redis import RedisClient
from app.core.security import create_access_token, create_refresh_token
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import TokenPair

DENYLIST_PREFIX = "denylist:jti:"


class TokenService:
    def __init__(self, session: AsyncSession, redis: RedisClient) -> None:
        self.session = session
        self.redis = redis

    async def issue_pair(
        self,
        user_id: int,
        permissions: set[int],
        family_id: uuid.UUID | None = None,
        device_id: int | None = None,
    ) -> TokenPair:
        family_id = family_id or uuid.uuid4()
        subject = str(user_id)

        access, _, _ = create_access_token(subject, extra_claims={"perms": sorted(permissions)})
        refresh, refresh_jti, refresh_exp = create_refresh_token(
            subject, extra_claims={"family": str(family_id)}
        )

        self.session.add(
            RefreshToken(
                user_id=user_id,
                jti=refresh_jti,
                family_id=family_id,
                expires_at=refresh_exp,
                device_id=device_id,
            )
        )
        await self.session.flush()

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def rotate(self, refresh_jti: str, user_id: int, permissions: set[int]) -> TokenPair:
        record = (
            await self.session.execute(select(RefreshToken).where(RefreshToken.jti == refresh_jti))
        ).scalar_one_or_none()

        if record is None or record.revoked:
            raise TokenRevokedError("Refresh token is not valid.")

        if record.rotated:
            await self._revoke_family(record.family_id)
            raise TokenRevokedError("Refresh token reuse detected; all sessions revoked.")

        record.rotated = True
        await self.session.flush()

        return await self.issue_pair(
            user_id=user_id,
            permissions=permissions,
            family_id=record.family_id,
            device_id=record.device_id,
        )

    async def revoke_access_jti(self, jti: str, expires_at: datetime) -> None:
        ttl = max(1, int((expires_at - datetime.now(UTC)).total_seconds()))
        await self.redis.set(f"{DENYLIST_PREFIX}{jti}", "1", ex=ttl)

    async def is_denylisted(self, jti: str) -> bool:
        return await self.redis.exists(f"{DENYLIST_PREFIX}{jti}") == 1

    async def _revoke_family(self, family_id: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.family_id == family_id).values(revoked=True)
        )
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        )
        await self.session.flush()
