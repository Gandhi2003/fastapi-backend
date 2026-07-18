from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import NotFoundError
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, repo: CategoryRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: CategoryCreate) -> Category:
        category = await self.repo.create(**payload.model_dump())
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def get(self, category_id: int) -> Category:
        category = await self.repo.get(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    async def list(self, params: PageParams) -> Page[Category]:
        return await self.repo.list(params)

    async def update(self, category_id: int, payload: CategoryUpdate) -> Category:
        category = await self.get(category_id)
        await self.repo.update(category, **payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: int) -> None:
        category = await self.get(category_id)
        await self.repo.soft_delete(category)
        await self.session.commit()
