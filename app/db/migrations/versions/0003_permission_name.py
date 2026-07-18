from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_permission_name"
down_revision: str | None = "0002_core_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("permissions", sa.Column("name", sa.String(150), nullable=True))
    op.execute(
        "UPDATE permissions "
        "SET name = initcap(action) || ' ' || replace(resource, '_', ' ') "
        "WHERE name IS NULL"
    )
    op.alter_column("permissions", "name", existing_type=sa.String(150), nullable=False)
    op.create_index("ix_permissions_name", "permissions", ["name"])


def downgrade() -> None:
    op.drop_index("ix_permissions_name", table_name="permissions")
    op.drop_column("permissions", "name")
