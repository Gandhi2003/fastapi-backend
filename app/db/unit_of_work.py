"""Unit of Work — owns the transaction boundary.

A service method may touch several repositories (e.g. create a user, assign a
role, write an audit log). The UoW guarantees they commit together or not at
all. Repositories only `flush`; the UoW `commit`s on success and `rollback`s on
any exception.

Repositories are lazily attached to the UoW so a service reaches every aggregate
through one object: `async with uow: await uow.users.create(...)`.
"""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


class UnitOfWork:
    """Transaction-scoped aggregate of repositories.

    Concrete UoWs (or a registry) wire up domain repositories as attributes.
    Kept generic here; modules access repositories they need via composition.
    """

    session: AsyncSession

    def __init__(self, session_factory=AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> UnitOfWork:
        self.session = self._session_factory()
        self._init_repositories()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.session.close()

    def _init_repositories(self) -> None:
        """Override in a concrete UoW to attach domain repositories.

        Example:
            from app.modules.users.repository import UserRepository
            self.users = UserRepository(session=self.session)
        """

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
