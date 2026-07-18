"""Role endpoints — manage roles and assign permissions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.permissions.repository import PermissionRepository
from app.modules.roles.repository import RoleRepository
from app.modules.roles.schemas import RoleCreate, RoleRead, RoleUpdate
from app.modules.roles.service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_service(session: AsyncSession = Depends(db_session)) -> RoleService:
    return RoleService(RoleRepository(session), PermissionRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    service: RoleService = Depends(get_service),
    _: CurrentUser = require_permissions("roles:create"),
) -> ResponseEnvelope[RoleRead]:
    role = await service.create(payload)
    return ok(RoleRead.model_validate(role))


@router.get("")
async def list_roles(
    params: PageParams = Depends(),
    service: RoleService = Depends(get_service),
    _: CurrentUser = require_permissions("roles:read"),
) -> ResponseEnvelope[list[RoleRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([RoleRead.model_validate(r) for r in page.items], meta=meta)


@router.get("/{role_id}")
async def get_role(
    role_id: int,
    service: RoleService = Depends(get_service),
    _: CurrentUser = require_permissions("roles:read"),
) -> ResponseEnvelope[RoleRead]:
    role = await service.get(role_id)
    return ok(RoleRead.model_validate(role))


@router.patch("/{role_id}")
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    service: RoleService = Depends(get_service),
    _: CurrentUser = require_permissions("roles:update"),
) -> ResponseEnvelope[RoleRead]:
    role = await service.update(role_id, payload)
    return ok(RoleRead.model_validate(role))


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
async def delete_role(
    role_id: int,
    service: RoleService = Depends(get_service),
    _: CurrentUser = require_permissions("roles:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(role_id)
    return ok({"detail": "Role deleted."})
