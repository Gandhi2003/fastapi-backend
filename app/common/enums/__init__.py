from __future__ import annotations

from enum import IntEnum, StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class ResourceType(IntEnum):
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
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4


def build_permission_code(resource: ResourceType, action: ActionType) -> int:
    return int(resource) * 10 + int(action)


def parse_permission_code(code: str) -> int:
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
