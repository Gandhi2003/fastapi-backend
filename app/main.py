from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis, init_redis
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.monitoring.metrics import PrometheusMiddleware, metrics_endpoint

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Startup/shutdown: own long-lived resources (Redis pool, etc.)."""
    configure_logging()
    init_redis()
    logger.info("app_startup", env=settings.ENVIRONMENT)
    yield
    await close_redis()
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
        # Hide internal docs in production behind the gateway/SSO if required.
    )

    # --- middleware (registered last runs first / outermost) -------------- #
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    # Signed cookie session — backs the OAuth state/nonce during the login dance.
    app.add_middleware(
        SessionMiddleware, secret_key=settings.SECRET_KEY, https_only=settings.is_production
    )
    app.add_middleware(RequestContextMiddleware)
    if settings.PROMETHEUS_ENABLED:
        app.add_middleware(PrometheusMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # --- error handling --------------------------------------------------- #
    register_exception_handlers(app)

    # --- routes ----------------------------------------------------------- #
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    if settings.PROMETHEUS_ENABLED:
        app.add_route("/metrics", metrics_endpoint, include_in_schema=False)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": settings.APP_NAME, "docs": "/docs"}

    return app


app = create_app()
