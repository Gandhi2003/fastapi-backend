"""Dealer service — business rules for the dealer aggregate."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import NotFoundError
from app.modules.dealers.models import Dealer
from app.modules.dealers.repository import DealerRepository
from app.modules.dealers.schemas import DealerCreate, DealerUpdate


class DealerService:
    def __init__(self, repo: DealerRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: DealerCreate, owner_id: int) -> Dealer:
        dealer = await self.repo.create(**payload.model_dump(), owner_id=owner_id)
        await self.session.commit()
        await self.session.refresh(dealer)
        return dealer

    async def get(self, dealer_id: int) -> Dealer:
        dealer = await self.repo.get(dealer_id)
        if dealer is None:
            raise NotFoundError("Dealer not found.")
        return dealer

    async def list(self, params: PageParams) -> Page[Dealer]:
        return await self.repo.list(params)

    async def update(self, dealer_id: int, payload: DealerUpdate) -> Dealer:
        dealer = await self.get(dealer_id)
        await self.repo.update(dealer, **payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(dealer)
        return dealer

    async def delete(self, dealer_id: int) -> None:
        dealer = await self.get(dealer_id)
        await self.repo.soft_delete(dealer)
        await self.session.commit()
