"""Declarative base + global metadata conventions.

A consistent constraint-naming convention is essential for Alembic to generate
stable, reversible migrations (otherwise Postgres auto-names indexes/constraints
and autogenerate produces noisy, non-deterministic diffs).

NOTE: every model module must be imported before `Base.metadata` is used for
autogenerate. `app/db/models_registry.py` centralizes those imports.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
