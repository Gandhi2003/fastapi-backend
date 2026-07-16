"""User entity and the user↔role association.

Carries authentication state (password hash, MFA secret, lockout counters,
verification timestamps) alongside profile fields. Soft-deletable so that
deleting a user preserves their audit trail and historical order/lead records.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import AuthProvider, UserStatus
from app.db.base import Base
from app.db.mixins import IntPkMixin, SoftDeleteMixin, TimestampMixin
from app.modules.roles.models import Role

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base, IntPkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    # Auth — hashed_password is nullable for OAuth-only accounts.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(
        String(20), default=AuthProvider.LOCAL, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        String(20), default=UserStatus.PENDING, nullable=False, index=True
    )

    # Email verification
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # MFA (TOTP)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Account lockout
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list[Role]] = relationship(secondary=user_roles, lazy="selectin")

    # --- convenience -------------------------------------------------------- #
    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def permission_codes(self) -> set[int]:
        """Flattened set of integer permission codes from all assigned roles.

        Superusers bypass the check via ``is_superuser`` (see require_permissions),
        so they don't need an explicit wildcard here.
        """
        return {perm.code for role in self.roles for perm in role.permissions}
