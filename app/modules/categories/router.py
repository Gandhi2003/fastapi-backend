from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.modules.categories.service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


def get_service(session: AsyncSession = Depends(db_session)) -> CategoryService:
    return CategoryService(CategoryRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    service: CategoryService = Depends(get_service),
    _: CurrentUser = require_permissions("categories:create"),
) -> ResponseEnvelope[CategoryRead]:
    category = await service.create(payload)
    return ok(CategoryRead.model_validate(category))


@router.get("")
async def list_categories(
    params: PageParams = Depends(),
    service: CategoryService = Depends(get_service),
    _: CurrentUser = require_permissions("categories:read"),
) -> ResponseEnvelope[list[CategoryRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([CategoryRead.model_validate(c) for c in page.items], meta=meta)


@router.get("/{category_id}")
async def get_category(
    category_id: int,
    service: CategoryService = Depends(get_service),
    _: CurrentUser = require_permissions("categories:read"),
) -> ResponseEnvelope[CategoryRead]:
    category = await service.get(category_id)
    return ok(CategoryRead.model_validate(category))


@router.patch("/{category_id}")
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: CategoryService = Depends(get_service),
    _: CurrentUser = require_permissions("categories:update"),
) -> ResponseEnvelope[CategoryRead]:
    category = await service.update(category_id, payload)
    return ok(CategoryRead.model_validate(category))


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_service),
    _: CurrentUser = require_permissions("categories:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(category_id)
    return ok({"detail": "Category deleted."})
