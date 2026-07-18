"""Supplier endpoints — CRUD following the customers template."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import SupplierCreate, SupplierRead, SupplierUpdate
from app.modules.suppliers.service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def get_service(session: AsyncSession = Depends(db_session)) -> SupplierService:
    return SupplierService(SupplierRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierCreate,
    service: SupplierService = Depends(get_service),
    user: CurrentUser = require_permissions("suppliers:create"),
) -> ResponseEnvelope[SupplierRead]:
    supplier = await service.create(payload, owner_id=user.id)
    return ok(SupplierRead.model_validate(supplier))


@router.get("")
async def list_suppliers(
    params: PageParams = Depends(),
    service: SupplierService = Depends(get_service),
    _: CurrentUser = require_permissions("suppliers:read"),
) -> ResponseEnvelope[list[SupplierRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([SupplierRead.model_validate(s) for s in page.items], meta=meta)


@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_service),
    _: CurrentUser = require_permissions("suppliers:read"),
) -> ResponseEnvelope[SupplierRead]:
    supplier = await service.get(supplier_id)
    return ok(SupplierRead.model_validate(supplier))


@router.patch("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    service: SupplierService = Depends(get_service),
    _: CurrentUser = require_permissions("suppliers:update"),
) -> ResponseEnvelope[SupplierRead]:
    supplier = await service.update(supplier_id, payload)
    return ok(SupplierRead.model_validate(supplier))


@router.delete("/{supplier_id}", status_code=status.HTTP_200_OK)
async def delete_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_service),
    _: CurrentUser = require_permissions("suppliers:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(supplier_id)
    return ok({"detail": "Supplier deleted."})
