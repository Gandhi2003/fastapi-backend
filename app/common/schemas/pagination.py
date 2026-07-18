from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = Field(default=20, ge=1, le=200, description="Items per page.")
    sort: str | None = Field(default=None, description="Column to sort by, e.g. 'created_at'.")
    order: Literal["asc", "desc"] = Field(default="desc")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return self.total + self.page_size - 1
