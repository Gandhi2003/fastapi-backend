"""Application exception hierarchy.

Services and repositories raise these domain exceptions. They carry an HTTP
status, a stable machine-readable `code`, and a human message. A single global
handler (see app/core/exception_handlers.py) translates them into the standard
error envelope, so business code never builds HTTP responses by hand.

Why a custom hierarchy instead of raising HTTPException everywhere:
  * the domain/service layer stays free of FastAPI imports (Clean Architecture);
  * stable `code` strings let frontends branch on errors without parsing prose;
  * one place owns the HTTP mapping, so it is consistent across 100+ modules.
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base class for all expected, handled application errors."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        super().__init__(self.message)


# --- 4xx ----------------------------------------------------------------- #
class BadRequestError(AppException):
    status_code = 400
    code = "bad_request"
    message = "The request was invalid."


class AuthenticationError(AppException):
    status_code = 401
    code = "unauthenticated"
    message = "Authentication required."


class PermissionDeniedError(AppException):
    status_code = 403
    code = "permission_denied"
    message = "You do not have permission to perform this action."


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"
    message = "The requested resource was not found."


class ConflictError(AppException):
    status_code = 409
    code = "conflict"
    message = "The resource already exists or conflicts with current state."


class ValidationError(AppException):
    status_code = 422
    code = "validation_error"
    message = "Validation failed."


class RateLimitError(AppException):
    status_code = 429
    code = "rate_limited"
    message = "Too many requests. Please slow down."


# --- Auth-specific specializations --------------------------------------- #
class InvalidCredentialsError(AuthenticationError):
    code = "invalid_credentials"
    message = "Incorrect email or password."


class AccountLockedError(AuthenticationError):
    code = "account_locked"
    message = "Account temporarily locked due to too many failed attempts."


class TokenRevokedError(AuthenticationError):
    code = "token_revoked"
    message = "This token has been revoked."


class MFARequiredError(AuthenticationError):
    code = "mfa_required"
    message = "Multi-factor authentication is required."


class EmailNotVerifiedError(AuthenticationError):
    code = "email_not_verified"
    message = "Please verify your email address before signing in."
