from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import NotFoundError
from app.modules.customers.models import Customer
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, repo: CustomerRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: CustomerCreate, owner_id: int) -> Customer:
        customer = await self.repo.create(**payload.model_dump(), owner_id=owner_id)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def get(self, customer_id: int) -> Customer:
        customer = await self.repo.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found.")
        return customer

    async def list(self, params: PageParams) -> Page[Customer]:
        return await self.repo.list(params)

    async def update(self, customer_id: int, payload: CustomerUpdate) -> Customer:
        customer = await self.get(customer_id)
        await self.repo.update(customer, **payload.model_dump(exclude_unset=True))
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def delete(self, customer_id: int) -> None:
        customer = await self.get(customer_id)
        await self.repo.soft_delete(customer)
        await self.session.commit()
