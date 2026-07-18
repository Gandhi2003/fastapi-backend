from __future__ import annotations

from typing import Any, cast

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=10,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
)
def send_email(self: Any, to: str, subject: str, body: str) -> dict[str, str]:
    logger.info("send_email", to=to, subject=subject, attempt=self.request.retries)
    return {"status": "sent", "to": to}


@celery_app.task
def send_verification_email(to: str, token: str) -> dict[str, str]:
    link = f"https://app.wealthified.in/verify-email?token={token}"
    return cast(
        "dict[str, str]",
        send_email.run(to, "Verify your email", f"Click to verify: {link}"),
    )
