"""Product repository — generic CRUD plus a name/SKU search."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.db.repositories.base import BaseRepository
from app.modules.products.models import Product


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    async def search(self, term: str, params: PageParams) -> Page[Product]:
        like = f"%{term}%"
        base = self._base_query().where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
        total = (
            await self.session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        stmt = self._apply_sort(base, params).offset(params.offset).limit(params.limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return Page(items=list(rows), total=total, page=params.page, page_size=params.page_size)
