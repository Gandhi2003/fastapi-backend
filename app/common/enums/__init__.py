"""Shared enums used across modules."""

from __future__ import annotations

from enum import IntEnum, StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"  # awaiting email verification
    SUSPENDED = "suspended"


class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class ResourceType(IntEnum):
    """The protectable resources — one per CRUD module.

    Stored as a SMALLINT in ``permissions.resource`` (1, 2, 3, …); the name↔number
    mapping lives here. Add a new member (next free number) when you add a module.
    """

    USERS = 1
    ROLES = 2
    PERMISSIONS = 3
    CUSTOMERS = 4
    FARMERS = 5
    DEALERS = 6
    SUPPLIERS = 7
    CATEGORIES = 8
    PRODUCTS = 9


class ActionType(IntEnum):
    """The operations a permission can grant. Stored as SMALLINT in ``permissions.action``."""

    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4


def build_permission_code(resource: ResourceType, action: ActionType) -> int:
    """Deterministic integer code for a permission = resource*10 + action.

    e.g. customers(4) + create(1) -> 41. Unique because action is always < 10.
    This integer is what's stored in ``permissions.code``.
    """
    return int(resource) * 10 + int(action)


def parse_permission_code(code: str) -> int:
    """Turn a readable "<resource>:<action>" string into its integer code.

    e.g. "customers:create" -> 41. Used so route declarations can stay readable
    (``require_permissions("customers:create")``) while the DB stores integers.
    """
    resource_name, action_name = code.split(":")
    return build_permission_code(
        ResourceType[resource_name.upper()], ActionType[action_name.upper()]
    )


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    WON = "won"
    LOST = "lost"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class KYCStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
