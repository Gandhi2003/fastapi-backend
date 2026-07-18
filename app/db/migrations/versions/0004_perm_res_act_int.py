from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004_perm_res_act_int"
down_revision: str | None = "0003_permission_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RESOURCE = {
    "users": 1,
    "roles": 2,
    "permissions": 3,
    "customers": 4,
    "farmers": 5,
    "dealers": 6,
    "suppliers": 7,
    "categories": 8,
    "products": 9,
}
_ACTION = {"create": 1, "read": 2, "update": 3, "delete": 4}


def _case(column: str, mapping: dict[str, int], *, to_int: bool) -> str:
    whens = []
    for text, num in mapping.items():
        if to_int:
            whens.append(f"WHEN '{text}' THEN {num}")
        else:
            whens.append(f"WHEN {num} THEN '{text}'")
    return f"CASE {column} " + " ".join(whens) + " END"


def upgrade() -> None:
    op.execute(
        f"ALTER TABLE permissions ALTER COLUMN resource TYPE smallint "
        f"USING ({_case('resource', _RESOURCE, to_int=True)})"
    )
    op.execute(
        f"ALTER TABLE permissions ALTER COLUMN action TYPE smallint "
        f"USING ({_case('action', _ACTION, to_int=True)})"
    )


def downgrade() -> None:
    op.execute(
        f"ALTER TABLE permissions ALTER COLUMN resource TYPE varchar(80) "
        f"USING ({_case('resource', _RESOURCE, to_int=False)})"
    )
    op.execute(
        f"ALTER TABLE permissions ALTER COLUMN action TYPE varchar(40) "
        f"USING ({_case('action', _ACTION, to_int=False)})"
    )
