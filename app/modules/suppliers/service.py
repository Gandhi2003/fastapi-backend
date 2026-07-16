"""Supplier service — business rules for the supplier aggregate."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import NotFoundError
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import SupplierCreate, SupplierUpdate


class SupplierService:
    def __init__(self, repo: SupplierRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: SupplierCreate, owner_id: int) -> Supplier:
        supplier = await self.repo.create(**payload.model_dump(), owner_id=owner_id)
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier

    async def get(self, supplier_id: int) -> Supplier:
        supplier = await self.repo.get(supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier not found.")
        return supplier

    async def list(self, params: PageParams) -> Page[Supplier]:
        return await self.repo.list(params)

    async def update(self, supplier_id: int, payload: SupplierUpdate) -> Supplier:
        supplier = await self.get(supplier_id)
        await self.repo.update(supplier, **payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier

    async def delete(self, supplier_id: int) -> None:
        supplier = await self.get(supplier_id)
        await self.repo.soft_delete(supplier)
        await self.session.commit()
