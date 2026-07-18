from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.customers.router import router as customers_router
from app.modules.dealers.router import router as dealers_router
from app.modules.farmers.router import router as farmers_router
from app.modules.health.router import router as health_router
from app.modules.permissions.router import router as permissions_router
from app.modules.products.router import router as products_router
from app.modules.roles.router import router as roles_router
from app.modules.suppliers.router import router as suppliers_router
from app.modules.users.router import router as users_router

api_router = APIRouter()


api_router.include_router(health_router)
api_router.include_router(auth_router)


api_router.include_router(permissions_router)
api_router.include_router(roles_router)
api_router.include_router(users_router)

api_router.include_router(customers_router)
api_router.include_router(farmers_router)
api_router.include_router(dealers_router)
api_router.include_router(suppliers_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
