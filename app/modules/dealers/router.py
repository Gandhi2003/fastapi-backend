"""Dealer endpoints — CRUD following the customers template."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.dealers.repository import DealerRepository
from app.modules.dealers.schemas import DealerCreate, DealerRead, DealerUpdate
from app.modules.dealers.service import DealerService

router = APIRouter(prefix="/dealers", tags=["Dealers"])


def get_service(session: AsyncSession = Depends(db_session)) -> DealerService:
    return DealerService(DealerRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dealer(
    payload: DealerCreate,
    service: DealerService = Depends(get_service),
    user: CurrentUser = require_permissions("dealers:create"),
) -> ResponseEnvelope[DealerRead]:
    dealer = await service.create(payload, owner_id=user.id)
    return ok(DealerRead.model_validate(dealer))


@router.get("")
async def list_dealers(
    params: PageParams = Depends(),
    service: DealerService = Depends(get_service),
    _: CurrentUser = require_permissions("dealers:read"),
) -> ResponseEnvelope[list[DealerRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([DealerRead.model_validate(d) for d in page.items], meta=meta)


@router.get("/{dealer_id}")
async def get_dealer(
    dealer_id: int,
    service: DealerService = Depends(get_service),
    _: CurrentUser = require_permissions("dealers:read"),
) -> ResponseEnvelope[DealerRead]:
    dealer = await service.get(dealer_id)
    return ok(DealerRead.model_validate(dealer))


@router.patch("/{dealer_id}")
async def update_dealer(
    dealer_id: int,
    payload: DealerUpdate,
    service: DealerService = Depends(get_service),
    _: CurrentUser = require_permissions("dealers:update"),
) -> ResponseEnvelope[DealerRead]:
    dealer = await service.update(dealer_id, payload)
    return ok(DealerRead.model_validate(dealer))


@router.delete("/{dealer_id}", status_code=status.HTTP_200_OK)
async def delete_dealer(
    dealer_id: int,
    service: DealerService = Depends(get_service),
    _: CurrentUser = require_permissions("dealers:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(dealer_id)
    return ok({"detail": "Dealer deleted."})
