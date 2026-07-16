"""Permission service — manage the authorization atoms."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import build_permission_code
from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.permissions.models import Permission
from app.modules.permissions.repository import PermissionRepository
from app.modules.permissions.schemas import PermissionCreate, PermissionUpdate


class PermissionService:
    def __init__(self, repo: PermissionRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def create(self, payload: PermissionCreate) -> Permission:
        code = build_permission_code(payload.resource, payload.action)
        if await self.repo.get_by_code(code):
            raise ConflictError("A permission for this resource+action already exists.")
        permission = await self.repo.create(**payload.model_dump(), code=code)
        await self.session.commit()
        await self.session.refresh(permission)
        return permission

    async def get(self, permission_id: int) -> Permission:
        permission = await self.repo.get(permission_id)
        if permission is None:
            raise NotFoundError("Permission not found.")
        return permission

    async def list(self, params: PageParams) -> Page[Permission]:
        return await self.repo.list(params)

    async def update(self, permission_id: int, payload: PermissionUpdate) -> Permission:
        permission = await self.get(permission_id)
        changes = payload.model_dump(exclude_unset=True)
        # If resource or action changed, re-derive the integer code and make sure
        # the new resource+action pair isn't already taken by another permission.
        if "resource" in changes or "action" in changes:
            resource = changes.get("resource", permission.resource)
            action = changes.get("action", permission.action)
            new_code = build_permission_code(resource, action)
            if new_code != permission.code:
                existing = await self.repo.get_by_code(new_code)
                if existing is not None:
                    raise ConflictError("A permission for this resource+action already exists.")
                changes["code"] = new_code
        await self.repo.update(permission, **changes)
        await self.session.commit()
        await self.session.refresh(permission)
        return permission

    async def delete(self, permission_id: int) -> None:
        permission = await self.get(permission_id)
        await self.repo.hard_delete(permission)  # no soft-delete on permissions
        await self.session.commit()
