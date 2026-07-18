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
    payload: ResponseEnvelope[None] = ResponseEnvelope(
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
        return _envelope(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "Request validation failed.",
            request,
            details=exc.errors(),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_exc(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("integrity_error", error=str(exc.orig))
        return _envelope(
            status.HTTP_409_CONFLICT,
            "conflict",
            "The operation conflicts with existing data.",
            request,
        )

    @app.exception_handler(Exception)
    async def _unhandled_exc(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return _envelope(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An unexpected error occurred.",
            request,
        )
