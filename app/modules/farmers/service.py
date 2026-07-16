"""Farmer service — business rules for the farmer aggregate."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import NotFoundError
from app.modules.farmers.models import Farmer
from app.modules.farmers.repository import FarmerRepository
from app.modules.farmers.schemas import FarmerCreate, FarmerUpdate


class FarmerService:
    def __init__(self, repo: FarmerRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: FarmerCreate, owner_id: int) -> Farmer:
        farmer = await self.repo.create(**payload.model_dump(), owner_id=owner_id)
        await self.session.commit()
        await self.session.refresh(farmer)
        return farmer

    async def get(self, farmer_id: int) -> Farmer:
        farmer = await self.repo.get(farmer_id)
        if farmer is None:
            raise NotFoundError("Farmer not found.")
        return farmer

    async def list(self, params: PageParams) -> Page[Farmer]:
        return await self.repo.list(params)

    async def update(self, farmer_id: int, payload: FarmerUpdate) -> Farmer:
        farmer = await self.get(farmer_id)
        await self.repo.update(farmer, **payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(farmer)
        return farmer

    async def delete(self, farmer_id: int) -> None:
        farmer = await self.get(farmer_id)
        await self.repo.soft_delete(farmer)
        await self.session.commit()
