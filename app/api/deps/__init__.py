"""Public dependency surface — import from here in routers."""

from app.api.deps.auth import (
    get_auth_service,
    get_current_user,
    get_token_service,
    get_user_repository,
    require_permissions,
)
from app.api.deps.database import db_session

__all__ = [
    "db_session",
    "get_auth_service",
    "get_current_user",
    "get_token_service",
    "get_user_repository",
    "require_permissions",
]
