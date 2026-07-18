"""Farmer endpoints — CRUD following the customers template."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.farmers.repository import FarmerRepository
from app.modules.farmers.schemas import FarmerCreate, FarmerRead, FarmerUpdate
from app.modules.farmers.service import FarmerService

router = APIRouter(prefix="/farmers", tags=["Farmers"])


def get_service(session: AsyncSession = Depends(db_session)) -> FarmerService:
    return FarmerService(FarmerRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_farmer(
    payload: FarmerCreate,
    service: FarmerService = Depends(get_service),
    user: CurrentUser = require_permissions("farmers:create"),
) -> ResponseEnvelope[FarmerRead]:
    farmer = await service.create(payload, owner_id=user.id)
    return ok(FarmerRead.model_validate(farmer))


@router.get("")
async def list_farmers(
    params: PageParams = Depends(),
    service: FarmerService = Depends(get_service),
    _: CurrentUser = require_permissions("farmers:read"),
) -> ResponseEnvelope[list[FarmerRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([FarmerRead.model_validate(f) for f in page.items], meta=meta)


@router.get("/{farmer_id}")
async def get_farmer(
    farmer_id: int,
    service: FarmerService = Depends(get_service),
    _: CurrentUser = require_permissions("farmers:read"),
) -> ResponseEnvelope[FarmerRead]:
    farmer = await service.get(farmer_id)
    return ok(FarmerRead.model_validate(farmer))


@router.patch("/{farmer_id}")
async def update_farmer(
    farmer_id: int,
    payload: FarmerUpdate,
    service: FarmerService = Depends(get_service),
    _: CurrentUser = require_permissions("farmers:update"),
) -> ResponseEnvelope[FarmerRead]:
    farmer = await service.update(farmer_id, payload)
    return ok(FarmerRead.model_validate(farmer))


@router.delete("/{farmer_id}", status_code=status.HTTP_200_OK)
async def delete_farmer(
    farmer_id: int,
    service: FarmerService = Depends(get_service),
    _: CurrentUser = require_permissions("farmers:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(farmer_id)
    return ok({"detail": "Farmer deleted."})
