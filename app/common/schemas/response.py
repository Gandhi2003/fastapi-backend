from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: object | None = Field(default=None, description="Field-level errors or extra context.")


class Meta(BaseModel):
    request_id: str | None = None
    page: int | None = None
    page_size: int | None = None
    total_items: int | None = None
    total_pages: int | None = None


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: ErrorDetail | None = None
    meta: Meta | None = None


def ok(data: T, meta: Meta | None = None) -> ResponseEnvelope[T]:
    return ResponseEnvelope[T](success=True, data=data, meta=meta)
