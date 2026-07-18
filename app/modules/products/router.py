from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.api.deps.database import db_session
from app.common.schemas.pagination import PageParams
from app.common.schemas.response import Meta, ResponseEnvelope, ok
from app.modules.auth.schemas import CurrentUser
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductRead, ProductUpdate
from app.modules.products.service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


def get_service(session: AsyncSession = Depends(db_session)) -> ProductService:
    return ProductService(ProductRepository(session), session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_service),
    _: CurrentUser = require_permissions("products:create"),
) -> ResponseEnvelope[ProductRead]:
    product = await service.create(payload)
    return ok(ProductRead.model_validate(product))


@router.get("")
async def list_products(
    params: PageParams = Depends(),
    service: ProductService = Depends(get_service),
    _: CurrentUser = require_permissions("products:read"),
) -> ResponseEnvelope[list[ProductRead]]:
    page = await service.list(params)
    meta = Meta(
        page=page.page,
        page_size=page.page_size,
        total_items=page.total,
        total_pages=page.total_pages,
    )
    return ok([ProductRead.model_validate(p) for p in page.items], meta=meta)


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_service),
    _: CurrentUser = require_permissions("products:read"),
) -> ResponseEnvelope[ProductRead]:
    product = await service.get(product_id)
    return ok(ProductRead.model_validate(product))


@router.patch("/{product_id}")
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(get_service),
    _: CurrentUser = require_permissions("products:update"),
) -> ResponseEnvelope[ProductRead]:
    product = await service.update(product_id, payload)
    return ok(ProductRead.model_validate(product))


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_service),
    _: CurrentUser = require_permissions("products:delete"),
) -> ResponseEnvelope[dict[str, str]]:
    await service.delete(product_id)
    return ok({"detail": "Product deleted."})
