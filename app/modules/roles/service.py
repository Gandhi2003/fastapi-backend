"""Role service — manage roles and their permission bundles."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.modules.permissions.repository import PermissionRepository
from app.modules.roles.models import Role
from app.modules.roles.repository import RoleRepository
from app.modules.roles.schemas import RoleCreate, RoleUpdate


class RoleService:
    def __init__(
        self,
        repo: RoleRepository,
        permissions: PermissionRepository,
        session: AsyncSession,
    ) -> None:
        self.repo = repo
        self.permissions = permissions
        self.session = session

    async def create(self, payload: RoleCreate) -> Role:
        if await self.repo.get_by_name(payload.name):
            raise ConflictError("A role with this name already exists.")
        role = Role(name=payload.name, description=payload.description)
        role.permissions = await self._resolve_permissions(payload.permission_ids)
        await self.repo.add(role)
        await self.session.commit()
        return await self._get_loaded(role.id)

    async def get(self, role_id: int) -> Role:
        role = await self.repo.get_with_permissions(role_id)
        if role is None:
            raise NotFoundError("Role not found.")
        return role

    async def list(self, params: PageParams) -> Page[Role]:
        # Role.permissions is lazy="selectin", so list rows arrive with perms loaded.
        return await self.repo.list(params)

    async def update(self, role_id: int, payload: RoleUpdate) -> Role:
        role = await self.get(role_id)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data and data["name"] != role.name:
            if await self.repo.get_by_name(data["name"]):
                raise ConflictError("A role with this name already exists.")
            role.name = data["name"]
        if "description" in data:
            role.description = data["description"]
        if payload.permission_ids is not None:
            role.permissions = await self._resolve_permissions(payload.permission_ids)

        await self.session.flush()
        await self.session.commit()
        return await self._get_loaded(role.id)

    async def delete(self, role_id: int) -> None:
        role = await self.get(role_id)
        if role.is_system:
            raise BadRequestError("System roles cannot be deleted.")
        await self.repo.hard_delete(role)  # no soft-delete on roles
        await self.session.commit()

    # --- helpers ---------------------------------------------------------- #
    async def _resolve_permissions(self, permission_ids: list[int]) -> list:
        if not permission_ids:
            return []
        perms = await self.permissions.get_many_by_ids(permission_ids)
        found = {p.id for p in perms}
        missing = set(permission_ids) - found
        if missing:
            raise BadRequestError(
                f"Unknown permission id(s): {', '.join(str(m) for m in sorted(missing, key=str))}"
            )
        return perms

    async def _get_loaded(self, role_id: int) -> Role:
        role = await self.repo.get_with_permissions(role_id)
        assert role is not None
        return role
