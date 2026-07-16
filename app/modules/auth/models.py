"""Auth persistence: refresh-token families, sessions and devices.

Refresh-token rotation with reuse detection (the OWASP-recommended pattern):
  * Each login starts a token "family" (``family_id``).
  * Every refresh issues a NEW refresh token and marks the old one ``rotated``.
  * If a token that was already rotated is presented again, it means the token
    leaked and is being replayed — we revoke the entire family, forcing re-login.

Sessions/devices give users a "where am I logged in" view and let admins or the
user revoke a specific device remotely.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IntPkMixin, TimestampMixin


class RefreshToken(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # jti of the issued JWT — links DB record to the signed token.
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # family_id groups all rotations of one login session. It's a random,
    # non-guessable token (NOT a table id), so it stays a UUID.
    family_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    device_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_devices.id", ondelete="SET NULL"), nullable=True
    )

    @property
    def is_active(self) -> bool:
        return not self.rotated and not self.revoked


class UserDevice(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "user_devices"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    device_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(400), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
