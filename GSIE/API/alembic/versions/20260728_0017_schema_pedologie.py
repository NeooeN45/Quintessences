"""Schema de domaine gsie_pedologie — RFC-0029 §4.1, GSIE-PROMPT-0027.

Cinquieme des sept schemas de domaine. La pedologie n'a pas encore de
table dediee dans le metamodele v6.2 : les donnees sols vivent dans les
tables transverses (`observation`, `sample`). Le schema est cree vide,
pret a recevoir les tables pedologiques futures (sols, horizons, reserve
utile — RRP, INRAE).

`gsie_application` recoit USAGE sur le schema et SELECT/INSERT/UPDATE sur
les tables futures (ALTER DEFAULT PRIVILEGES) — jamais DELETE (CON-010).

Revision ID: 20260728_0017
Revises: 20260728_0016
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0017"
down_revision: str | None = "20260728_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_pedologie"
_ROLE_APPLICATION = "gsie_application"
_ECRITURE = "SELECT, INSERT, UPDATE"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"GRANT {_ECRITURE} ON TABLES TO {_ROLE_APPLICATION}"
    )

    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA} IS "
        "'Domaine pedologie : sols, horizons, reserve utile. "
        "RFC-0029 §4.1. Schema vide en v6.2 — tables futures.'"
    )


def downgrade() -> None:
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"REVOKE {_ECRITURE} ON TABLES FROM {_ROLE_APPLICATION}"
    )

    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")
