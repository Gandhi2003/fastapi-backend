"""API v1 aggregate router.

Every module exposes an ``APIRouter`` named ``router``; they are mounted here
under the versioned prefix. Versioning at the router level (``/api/v1``) lets a
``/api/v2`` evolve in parallel without breaking existing clients — add a sibling
``app/api/v2/router`` package and mount it in main.py.
"""

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

# Health first so probes work even before auth is configured.
api_router.include_router(health_router)
api_router.include_router(auth_router)

# --- RBAC administration ---------------------------------------------------- #
api_router.include_router(permissions_router)
api_router.include_router(roles_router)
api_router.include_router(users_router)

# --- CRM domain ------------------------------------------------------------- #
api_router.include_router(customers_router)
api_router.include_router(farmers_router)
api_router.include_router(dealers_router)
api_router.include_router(suppliers_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)

# As more modules ship, mount them here. Each follows the same model→...→router slice:
# api_router.include_router(leads_router)
# api_router.include_router(orders_router)
# api_router.include_router(kyc_router)
# api_router.include_router(notifications_router)
# api_router.include_router(reports_router)
# api_router.include_router(audit_logs_router)
# api_router.include_router(file_uploads_router)
