"""Custom SQLAlchemy column types shared across models."""

from __future__ import annotations

from enum import IntEnum

from sqlalchemy import SmallInteger
from sqlalchemy.types import TypeDecorator


class IntEnumType(TypeDecorator):
    """Store a Python ``IntEnum`` as a SMALLINT column.

    The database holds the integer (1, 2, 3, …) — nice and compact, and what you
    see in pgAdmin — while Python always gets the enum member back, so app code
    can use ``ResourceType.CUSTOMERS`` instead of a magic number.
    """

    impl = SmallInteger
    cache_ok = True

    def __init__(self, enum_cls: type[IntEnum], *args, **kwargs) -> None:
        self._enum_cls = enum_cls
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):  # Python -> DB
        if value is None:
            return None
        # Accept an enum member, or a raw int/str that names a valid member.
        return self._enum_cls(value).value

    def process_result_value(self, value, dialect):  # DB -> Python
        if value is None:
            return None
        return self._enum_cls(value)
