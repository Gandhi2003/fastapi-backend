"""Generic async CRUD repository (Repository Pattern).

The repository is the ONLY place that knows about SQLAlchemy. Services depend on
this abstraction, not on the ORM, which keeps business logic persistence-agnostic
and trivially mockable in unit tests.

A single generic implementation gives all 100+ entities consistent CRUD,
soft-delete filtering, pagination, sorting and filtering — the DRY payoff of the
pattern. Modules subclass it only to add entity-specific queries.

Note: the repository never commits. Commit/rollback is owned by the Unit of Work
so that a single service method spanning several repositories is one atomic
transaction.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page, PageParams
from app.db.base import Base
from app.db.mixins import SoftDeleteMixin

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # --- internal helpers ------------------------------------------------- #
    def _base_query(self, include_deleted: bool = False) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        if issubclass(self.model, SoftDeleteMixin) and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        return stmt

    def _apply_filters(
        self, stmt: Select[tuple[ModelT]], filters: dict[str, Any] | None
    ) -> Select[tuple[ModelT]]:
        """Whitelist-by-attribute equality filtering. Extend per-repo for ranges/LIKE."""
        if not filters:
            return stmt
        for field, value in filters.items():
            column = getattr(self.model, field, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        return stmt

    def _apply_sort(self, stmt: Select[tuple[ModelT]], params: PageParams) -> Select[tuple[ModelT]]:
        sort_col = getattr(self.model, params.sort, None) if params.sort else None
        if sort_col is None:
            sort_col = getattr(self.model, "created_at", None)
        if sort_col is not None:
            stmt = stmt.order_by(asc(sort_col) if params.order == "asc" else desc(sort_col))
        return stmt

    # --- reads ------------------------------------------------------------ #
    async def get(self, id_: int, include_deleted: bool = False) -> ModelT | None:
        stmt = self._base_query(include_deleted).where(self.model.id == id_)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(self, **kwargs: Any) -> ModelT | None:
        stmt = self._apply_filters(self._base_query(), kwargs)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        params: PageParams,
        filters: dict[str, Any] | None = None,
    ) -> Page[ModelT]:
        base = self._apply_filters(self._base_query(), filters)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = self._apply_sort(base, params).offset(params.offset).limit(params.limit)
        rows = (await self.session.execute(stmt)).scalars().all()

        return Page(items=list(rows), total=total, page=params.page, page_size=params.page_size)

    async def exists(self, **kwargs: Any) -> bool:
        return await self.get_by(**kwargs) is not None

    # --- writes (flush only; UoW commits) --------------------------------- #
    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()  # populate PK/defaults without committing
        return instance

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: ModelT, **data: Any) -> ModelT:
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def soft_delete(self, instance: ModelT) -> None:
        if not isinstance(instance, SoftDeleteMixin):
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        instance.deleted_at = func.now()
        await self.session.flush()

    async def hard_delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
