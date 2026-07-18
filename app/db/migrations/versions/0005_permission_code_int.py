from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005_permission_code_int"
down_revision: str | None = "0004_perm_res_act_int"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RESOURCE = {
    1: "users",
    2: "roles",
    3: "permissions",
    4: "customers",
    5: "farmers",
    6: "dealers",
    7: "suppliers",
    8: "categories",
    9: "products",
}
_ACTION = {1: "create", 2: "read", 3: "update", 4: "delete"}


def upgrade() -> None:
    op.execute(
        "ALTER TABLE permissions ALTER COLUMN code TYPE integer USING (resource * 10 + action)"
    )


def downgrade() -> None:
    res_case = (
        "CASE resource " + " ".join(f"WHEN {n} THEN '{t}'" for n, t in _RESOURCE.items()) + " END"
    )
    act_case = (
        "CASE action " + " ".join(f"WHEN {n} THEN '{t}'" for n, t in _ACTION.items()) + " END"
    )
    op.execute(
        f"ALTER TABLE permissions ALTER COLUMN code TYPE varchar(150) "
        f"USING (({res_case}) || ':' || ({act_case}))"
    )
