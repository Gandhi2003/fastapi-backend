"""Email delivery tasks (verification, password reset, notifications).

Tasks are idempotent where possible and retry with exponential backoff on
transient SMTP failures. The web layer only enqueues — it never blocks on SMTP.
"""

from __future__ import annotations

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
def send_email(self, to: str, subject: str, body: str) -> dict:
    """Send a transactional email via SMTP. Replace body with a real SMTP call."""
    logger.info("send_email", to=to, subject=subject, attempt=self.request.retries)
    # smtplib / aiosmtplib call goes here.
    return {"status": "sent", "to": to}


@celery_app.task
def send_verification_email(to: str, token: str) -> dict:
    link = f"https://app.wealthified.in/verify-email?token={token}"
    return send_email.run(to, "Verify your email", f"Click to verify: {link}")
