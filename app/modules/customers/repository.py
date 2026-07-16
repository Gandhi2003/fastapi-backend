"""Customer repository. Inherits all CRUD/pagination/soft-delete from the base.

Most modules need nothing more than this subclass; add methods only for
entity-specific queries (e.g. full-text search, owner-scoped lists).
"""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.db.repositories.base import BaseRepository
from app.modules.customers.models import Customer


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Customer, session)

    async def search(self, term: str, params: PageParams) -> Page[Customer]:
        """Case-insensitive search across name/email/company."""
        like = f"%{term}%"
        base = self._base_query().where(
            or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.company.ilike(like),
            )
        )
        from sqlalchemy import func, select

        total = (
            await self.session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        stmt = self._apply_sort(base, params).offset(params.offset).limit(params.limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return Page(items=list(rows), total=total, page=params.page, page_size=params.page_size)
