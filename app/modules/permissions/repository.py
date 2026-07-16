"""Permission repository — generic CRUD plus id/code lookups for RBAC wiring."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.modules.permissions.models import Permission


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Permission, session)

    async def get_by_code(self, code: int) -> Permission | None:
        return await self.get_by(code=code)

    async def get_many_by_ids(self, ids: Sequence[int]) -> list[Permission]:
        if not ids:
            return []
        stmt = self._base_query().where(Permission.id.in_(ids))
        return list((await self.session.execute(stmt)).scalars().all())
