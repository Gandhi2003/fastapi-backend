"""Celery application — async background processing.

Offloads slow / unreliable work off the request path: sending emails, generating
reports, KYC document processing, webhook delivery, scheduled cleanups. Redis is
broker + result backend. Run with:
    celery -A app.workers.celery_app worker -l info
    celery -A app.workers.celery_app beat -l info   # for scheduled tasks
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "crm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.email",
        "app.workers.tasks.audit",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,  # redeliver if a worker dies mid-task
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # fair dispatch for long tasks
    task_track_started=True,
    result_expires=3600,
)

# Periodic schedule (celery beat). Example: nightly token cleanup.
celery_app.conf.beat_schedule = {
    "purge-expired-refresh-tokens": {
        "task": "app.workers.tasks.audit.purge_expired_tokens",
        "schedule": 24 * 60 * 60,
    },
}
