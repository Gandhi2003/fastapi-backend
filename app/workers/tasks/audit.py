from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task
def record_audit_event(
    actor_id: str | None, action: str, target: str, meta: dict[str, Any]
) -> None:
    logger.info("audit_event", actor=actor_id, action=action, target=target, meta=meta)


@celery_app.task
def purge_expired_tokens() -> int:
    logger.info("purge_expired_tokens_started")
    return 0
