"""Structured logging configuration using structlog.

Production emits one JSON object per line (ingestible by Loki/ELK/Datadog).
Local emits colourised, human-readable lines. A `request_id` contextvar is bound
per-request by middleware so every log line within a request is correlated.

structlog feeds records into stdlib ``logging`` so both app logs and framework
logs (uvicorn, sqlalchemy) share the same handlers: the console (stdout) plus,
when ``LOG_FILE`` is set, a rotating file (``logs/api.log`` by default). The file
is always JSON; the console follows ``LOG_JSON``.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any, cast

import structlog

from app.core.config import settings

# Correlation id, populated by RequestContextMiddleware and read by the processor.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def _add_request_id(
    _: Any, __: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    rid = request_id_ctx.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def _formatter(json: bool, shared: list[structlog.types.Processor]) -> logging.Formatter:
    """Build a stdlib formatter that renders structlog events (app + framework)."""
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer(colors=True)
    )
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,  # applied to stdlib records (uvicorn, sqlalchemy)
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )


def configure_logging() -> None:
    """Idempotent logging setup; call once during app/worker startup."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_request_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # structlog hands off to stdlib logging, which owns the handlers below.
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handlers: list[logging.Handler] = []

    # Console: human-readable locally, JSON in production (per LOG_JSON).
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(_formatter(settings.LOG_JSON, shared_processors))
    handlers.append(console)

    # Rotating file: always JSON so it stays machine-ingestible.
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=settings.LOG_FILE_MAX_BYTES,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(_formatter(json=True, shared=shared_processors))
        handlers.append(file_handler)

    root = logging.getLogger()
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL)

    # Let uvicorn/sqlalchemy propagate to the root handlers instead of their own.
    for noisy in ("uvicorn", "uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        noisy_logger = logging.getLogger(noisy)
        noisy_logger.handlers.clear()
        noisy_logger.propagate = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
