"""User repository — entity-specific queries on top of the generic CRUD base."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.modules.users.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            self._base_query().where(User.email == email.lower()).options(selectinload(User.roles))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_with_roles(self, user_id) -> User | None:
        stmt = self._base_query().where(User.id == user_id).options(selectinload(User.roles))
        return (await self.session.execute(stmt)).scalar_one_or_none()
