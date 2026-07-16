"""Customer endpoints — the canonical CRUD router template (copy per module).

Every route enforces a fine-grained permission via `require_permissions`. List
responses include pagination metadata in the envelope's `meta`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate
from app.modules.customers.service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_service(session: AsyncSession = Depends(db_session)) -> CustomerService:
    return CustomerService(CustomerRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    service: CustomerService = Depends(get_service),
    user: CurrentUser = require_permissions("customers:create"),
) -> ResponseEnvelope[CustomerRead]:
    customer = await service.create(payload, owner_id=user.id)
    return ok(CustomerRead.model_validate(customer))


@router.get("")
async def list_customers(
    params: PageParams = Depends(),
    service: CustomerService = Depends(get_service),
    _: CurrentUser = require_permissions("customers:read"),
) -> ResponseEnvelope[list[CustomerRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([CustomerRead.model_validate(c) for c in page.items], meta=meta)


@router.get("/{customer_id}")
async def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_service),
    _: CurrentUser = require_permissions("customers:read"),
) -> ResponseEnvelope[CustomerRead]:
    customer = await service.get(customer_id)
    return ok(CustomerRead.model_validate(customer))


@router.patch("/{customer_id}")
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    service: CustomerService = Depends(get_service),
    _: CurrentUser = require_permissions("customers:update"),
) -> ResponseEnvelope[CustomerRead]:
    customer = await service.update(customer_id, payload)
    return ok(CustomerRead.model_validate(customer))


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: int,
    service: CustomerService = Depends(get_service),
    _: CurrentUser = require_permissions("customers:delete"),
) -> ResponseEnvelope[dict]:
    await service.delete(customer_id)
    return ok({"detail": "Customer deleted."})
