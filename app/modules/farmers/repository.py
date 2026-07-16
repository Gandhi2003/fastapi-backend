"""Farmer repository — generic CRUD from the base."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.modules.farmers.models import Farmer


class FarmerRepository(BaseRepository[Farmer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Farmer, session)
