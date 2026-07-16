"""Role repository — CRUD plus eager permission loading and id lookups."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.modules.roles.models import Role


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Role, session)

    async def get_by_name(self, name: str) -> Role | None:
        return await self.get_by(name=name)

    async def get_with_permissions(self, role_id: int) -> Role | None:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_many_by_ids(self, ids: Sequence[int]) -> list[Role]:
        if not ids:
            return []
        stmt = select(Role).where(Role.id.in_(ids))
        return list((await self.session.execute(stmt)).scalars().all())
