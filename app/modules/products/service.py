from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import NotFoundError
from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, repo: ProductRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: ProductCreate) -> Product:
        product = await self.repo.create(**payload.model_dump())
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get(self, product_id: int) -> Product:
        product = await self.repo.get(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    async def list(self, params: PageParams) -> Page[Product]:
        return await self.repo.list(params)

    async def update(self, product_id: int, payload: ProductUpdate) -> Product:
        product = await self.get(product_id)
        await self.repo.update(product, **payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: int) -> None:
        product = await self.get(product_id)
        await self.repo.soft_delete(product)
        await self.session.commit()
