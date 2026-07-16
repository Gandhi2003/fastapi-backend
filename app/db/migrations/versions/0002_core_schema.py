"""core schema: rbac, auth, and core CRM tables

Revision ID: 0002_core_schema
Revises: 0001_enable_extensions
Create Date: 2026-06-28 00:00:00

Creates the full baseline schema: permissions/roles/users (RBAC), refresh tokens
& devices (auth), and the core CRM domain tables (customers, farmers, dealers,
suppliers, categories, products).

You can regenerate/extend this with autogenerate once the DB exists:
    alembic revision --autogenerate -m "..."
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_core_schema"
down_revision: str | None = "0001_enable_extensions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)  # still used for refresh_tokens.family_id
_NOW = sa.text("now()")


def _pk() -> sa.Column:
    # Auto-incrementing BIGSERIAL primary key: 1, 2, 3, ...
    return sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


def _deleted_at() -> sa.Column:
    return sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)


def upgrade() -> None:
    # --- permissions ------------------------------------------------------- #
    op.create_table(
        "permissions",
        _pk(),
        sa.Column("code", sa.String(150), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("resource", sa.String(80), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_index("ix_permissions_created_at", "permissions", ["created_at"])

    # --- roles ------------------------------------------------------------- #
    op.create_table(
        "roles",
        _pk(),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_index("ix_roles_created_at", "roles", ["created_at"])

    # --- role_permissions (M2M) ------------------------------------------- #
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.BigInteger,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            sa.BigInteger,
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # --- users ------------------------------------------------------------- #
    op.create_table(
        "users",
        _pk(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("auth_provider", sa.String(20), server_default="local", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column(
            "failed_login_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    # --- user_roles (M2M) -------------------------------------------------- #
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.BigInteger,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # --- user_devices ------------------------------------------------------ #
    op.create_table(
        "user_devices",
        _pk(),
        sa.Column(
            "user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("device_name", sa.String(150), nullable=True),
        sa.Column("user_agent", sa.String(400), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trusted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"])
    op.create_index("ix_user_devices_created_at", "user_devices", ["created_at"])

    # --- refresh_tokens ---------------------------------------------------- #
    op.create_table(
        "refresh_tokens",
        _pk(),
        sa.Column(
            "user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column("family_id", UUID, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "device_id",
            sa.BigInteger,
            sa.ForeignKey("user_devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamps(),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_index("ix_refresh_tokens_created_at", "refresh_tokens", ["created_at"])

    # --- customers --------------------------------------------------------- #
    op.create_table(
        "customers",
        _pk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column(
            "owner_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_customers_name", "customers", ["name"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_company", "customers", ["company"])
    op.create_index("ix_customers_owner_id", "customers", ["owner_id"])
    op.create_index("ix_customers_created_at", "customers", ["created_at"])
    op.create_index("ix_customers_deleted_at", "customers", ["deleted_at"])

    # --- categories -------------------------------------------------------- #
    op.create_table(
        "categories",
        _pk(),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    op.create_index("ix_categories_created_at", "categories", ["created_at"])
    op.create_index("ix_categories_deleted_at", "categories", ["deleted_at"])

    # --- products ---------------------------------------------------------- #
    op.create_table(
        "products",
        _pk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("unit", sa.String(40), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "category_id",
            sa.BigInteger,
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_created_at", "products", ["created_at"])
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"])

    # --- farmers ----------------------------------------------------------- #
    op.create_table(
        "farmers",
        _pk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("village", sa.String(150), nullable=True),
        sa.Column("district", sa.String(150), nullable=True),
        sa.Column("state", sa.String(150), nullable=True),
        sa.Column("land_size_acres", sa.Numeric(10, 2), nullable=True),
        sa.Column("primary_crop", sa.String(120), nullable=True),
        sa.Column(
            "owner_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_farmers_name", "farmers", ["name"])
    op.create_index("ix_farmers_phone", "farmers", ["phone"])
    op.create_index("ix_farmers_district", "farmers", ["district"])
    op.create_index("ix_farmers_owner_id", "farmers", ["owner_id"])
    op.create_index("ix_farmers_created_at", "farmers", ["created_at"])
    op.create_index("ix_farmers_deleted_at", "farmers", ["deleted_at"])

    # --- dealers ----------------------------------------------------------- #
    op.create_table(
        "dealers",
        _pk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("region", sa.String(150), nullable=True),
        sa.Column("gst_number", sa.String(20), nullable=True),
        sa.Column(
            "owner_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_dealers_name", "dealers", ["name"])
    op.create_index("ix_dealers_company", "dealers", ["company"])
    op.create_index("ix_dealers_email", "dealers", ["email"])
    op.create_index("ix_dealers_region", "dealers", ["region"])
    op.create_index("ix_dealers_owner_id", "dealers", ["owner_id"])
    op.create_index("ix_dealers_created_at", "dealers", ["created_at"])
    op.create_index("ix_dealers_deleted_at", "dealers", ["deleted_at"])

    # --- suppliers --------------------------------------------------------- #
    op.create_table(
        "suppliers",
        _pk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column(
            "owner_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        *_timestamps(),
        _deleted_at(),
    )
    op.create_index("ix_suppliers_name", "suppliers", ["name"])
    op.create_index("ix_suppliers_company", "suppliers", ["company"])
    op.create_index("ix_suppliers_email", "suppliers", ["email"])
    op.create_index("ix_suppliers_owner_id", "suppliers", ["owner_id"])
    op.create_index("ix_suppliers_created_at", "suppliers", ["created_at"])
    op.create_index("ix_suppliers_deleted_at", "suppliers", ["deleted_at"])


def downgrade() -> None:
    for table in (
        "suppliers",
        "dealers",
        "farmers",
        "products",
        "categories",
        "customers",
        "refresh_tokens",
        "user_devices",
        "user_roles",
        "users",
        "role_permissions",
        "roles",
        "permissions",
    ):
        op.drop_table(table)
