from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.permissions.repository import PermissionRepository
from app.modules.permissions.schemas import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)
from app.modules.permissions.service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


def get_service(session: AsyncSession = Depends(db_session)) -> PermissionService:
    return PermissionService(PermissionRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    service: PermissionService = Depends(get_service),
    _: CurrentUser = require_permissions("permissions:create"),
) -> ResponseEnvelope[PermissionRead]:
    permission = await service.create(payload)
    return ok(PermissionRead.model_validate(permission))


@router.get("")
async def list_permissions(
    params: PageParams = Depends(),
    service: PermissionService = Depends(get_service),
    _: CurrentUser = require_permissions("permissions:read"),
) -> ResponseEnvelope[list[PermissionRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([PermissionRead.model_validate(p) for p in page.items], meta=meta)


@router.get("/{permission_id}")
async def get_permission(
    permission_id: int,
    service: PermissionService = Depends(get_service),
    _: CurrentUser = require_permissions("permissions:read"),
) -> ResponseEnvelope[PermissionRead]:
    permission = await service.get(permission_id)
    return ok(PermissionRead.model_validate(permission))


@router.patch("/{permission_id}")
async def update_permission(
    permission_id: int,
    payload: PermissionUpdate,
    service: PermissionService = Depends(get_service),
    _: CurrentUser = require_permissions("permissions:update"),
) -> ResponseEnvelope[PermissionRead]:
    permission = await service.update(permission_id, payload)
    return ok(PermissionRead.model_validate(permission))


@router.delete("/{permission_id}", status_code=status.HTTP_200_OK)
async def delete_permission(
    permission_id: int,
    service: PermissionService = Depends(get_service),
    _: CurrentUser = require_permissions("permissions:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(permission_id)
    return ok({"detail": "Permission deleted."})
