"""User admin endpoints — manage staff accounts and their roles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_service(session: AsyncSession = Depends(db_session)) -> UserService:
    return UserService(UserRepository(session), RoleRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_service),
    _: CurrentUser = require_permissions("users:create"),
) -> ResponseEnvelope[UserRead]:
    user = await service.create(payload)
    return ok(UserRead.model_validate(user))


@router.get("")
async def list_users(
    params: PageParams = Depends(),
    service: UserService = Depends(get_service),
    _: CurrentUser = require_permissions("users:read"),
) -> ResponseEnvelope[list[UserRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([UserRead.model_validate(u) for u in page.items], meta=meta)


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_service),
    _: CurrentUser = require_permissions("users:read"),
) -> ResponseEnvelope[UserRead]:
    user = await service.get(user_id)
    return ok(UserRead.model_validate(user))


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_service),
    _: CurrentUser = require_permissions("users:update"),
) -> ResponseEnvelope[UserRead]:
    user = await service.update(user_id, payload)
    return ok(UserRead.model_validate(user))


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_service),
    _: CurrentUser = require_permissions("users:delete"),
) -> ResponseEnvelope[dict]:
    await service.delete(user_id)
    return ok({"detail": "User deleted."})
