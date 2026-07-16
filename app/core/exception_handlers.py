"""Global exception handlers — the single place HTTP error responses are built.

Registered on the FastAPI app at startup. Guarantees:
  * every error leaves the API in the standard envelope shape;
  * internal exceptions never leak stack traces or SQL to clients;
  * everything is logged with the request id for correlation.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.common.schemas.response import ErrorDetail, Meta, ResponseEnvelope
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


def _envelope(
    status_code: int, code: str, message: str, request: Request, details: object = None
) -> JSONResponse:
    payload = ResponseEnvelope(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        meta=Meta(request_id=getattr(request.state, "request_id", None)),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _app_exc(request: Request, exc: AppException) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("app_exception", code=exc.code, message=exc.message)
        return _envelope(exc.status_code, exc.code, exc.message, request, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic produced structured field errors — surface them safely.
        return _envelope(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "Request validation failed.",
            request,
            details=exc.errors(),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_exc(request: Request, exc: IntegrityError) -> JSONResponse:
        # Unique/foreign-key violations → 409 without leaking the SQL.
        logger.warning("integrity_error", error=str(exc.orig))
        return _envelope(
            status.HTTP_409_CONFLICT,
            "conflict",
            "The operation conflicts with existing data.",
            request,
        )

    @app.exception_handler(Exception)
    async def _unhandled_exc(request: Request, exc: Exception) -> JSONResponse:
        # Last line of defence — log full detail server-side, return opaque 500.
        logger.exception("unhandled_exception", error=str(exc))
        return _envelope(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An unexpected error occurred.",
            request,
        )
