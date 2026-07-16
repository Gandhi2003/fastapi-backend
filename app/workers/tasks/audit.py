"""Audit & maintenance tasks."""

from __future__ import annotations

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task
def record_audit_event(actor_id: str | None, action: str, target: str, meta: dict) -> None:
    """Persist an audit log row off the request path (fire-and-forget)."""
    logger.info("audit_event", actor=actor_id, action=action, target=target, meta=meta)
    # Open a sync session and INSERT into audit_logs here.


@celery_app.task
def purge_expired_tokens() -> int:
    """Scheduled cleanup of expired/rotated refresh tokens (celery beat)."""
    logger.info("purge_expired_tokens_started")
    # DELETE FROM refresh_tokens WHERE expires_at < now() OR rotated OR revoked
    return 0
