"""User admin service — CRUD + role assignment for the users aggregate.

Distinct from the auth *registration* flow: this is administrative user
management (create staff, assign roles, suspend accounts). Admin-created users
are activated and email-verified immediately so they can sign in.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuthProvider
from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        roles: RoleRepository,
        session: AsyncSession,
    ) -> None:
        self.repo = repo
        self.roles = roles
        self.session = session

    async def create(self, payload: UserCreate) -> User:
        if await self.repo.get_by_email(payload.email):
            raise ConflictError("An account with this email already exists.")

        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            auth_provider=AuthProvider.LOCAL,
            status=payload.status,
            is_superuser=payload.is_superuser,
            email_verified_at=datetime.now(UTC),  # admin-created → pre-verified
        )
        user.roles = await self._resolve_roles(payload.role_ids)
        await self.repo.add(user)
        await self.session.commit()
        return await self._get_loaded(user.id)

    async def get(self, user_id: int) -> User:
        user = await self.repo.get_with_roles(user_id)
        if user is None or user.is_deleted:
            raise NotFoundError("User not found.")
        return user

    async def list(self, params: PageParams) -> Page[User]:
        # User.roles is lazy="selectin", so list rows arrive with roles loaded.
        return await self.repo.list(params)

    async def update(self, user_id: int, payload: UserUpdate) -> User:
        user = await self.get(user_id)
        data = payload.model_dump(exclude_unset=True)

        if "full_name" in data:
            user.full_name = data["full_name"]
        if "status" in data:
            user.status = data["status"]
        if "is_superuser" in data:
            user.is_superuser = data["is_superuser"]
        if data.get("password"):
            user.hashed_password = hash_password(data["password"])
        if payload.role_ids is not None:
            user.roles = await self._resolve_roles(payload.role_ids)

        await self.session.flush()
        await self.session.commit()
        return await self._get_loaded(user.id)

    async def delete(self, user_id: int) -> None:
        user = await self.get(user_id)
        await self.repo.soft_delete(user)
        await self.session.commit()

    # --- helpers ---------------------------------------------------------- #
    async def _resolve_roles(self, role_ids: list[int]) -> list:
        if not role_ids:
            return []
        roles = await self.roles.get_many_by_ids(role_ids)
        missing = set(role_ids) - {r.id for r in roles}
        if missing:
            raise BadRequestError(
                f"Unknown role id(s): {', '.join(str(m) for m in sorted(missing, key=str))}"
            )
        return roles

    async def _get_loaded(self, user_id: int) -> User:
        user = await self.repo.get_with_roles(user_id)
        assert user is not None
        return user
