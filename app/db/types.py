from __future__ import annotations

from enum import IntEnum
from typing import Any

from sqlalchemy import Dialect, SmallInteger
from sqlalchemy.types import TypeDecorator


class IntEnumType(TypeDecorator[IntEnum]):
    impl = SmallInteger
    cache_ok = True

    def __init__(self, enum_cls: type[IntEnum], *args: Any, **kwargs: Any) -> None:
        self._enum_cls = enum_cls
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Any, dialect: Dialect) -> int | None:  # Python -> DB
        if value is None:
            return None
        return self._enum_cls(value).value

    def process_result_value(self, value: Any, dialect: Dialect) -> IntEnum | None:  # DB -> Python
        if value is None:
            return None
        return self._enum_cls(value)
