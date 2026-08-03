"""Schema de domaine gsie_feu — RFC-0029 §4.1, GSIE-PROMPT-0027.

Septieme et dernier schema de domaine. Le feu n'a pas encore de table
dediee dans le metamodele v6.2 : les donnees incendie vivent dans les
tables transverses (`phenomenon` avec wildfire, `scenario`). Le schema est
cree vide, pret a recevoir les tables feu futures (historique d'incendies,
indices de danger, combustibles — Ignis).

`gsie_application` recoit USAGE sur le schema et SELECT/INSERT/UPDATE sur
les tables futures (ALTER DEFAULT PRIVILEGES) — jamais DELETE (CON-010).

Revision ID: 20260728_0019
Revises: 20260728_0018
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0019"
down_revision: str | None = "20260728_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_feu"
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
        "'Domaine feu : historique d incendies, indices de danger, "
        "combustibles. RFC-0029 §4.1. Schema vide en v6.2 — tables futures.'"
    )


def downgrade() -> None:
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"REVOKE {_ECRITURE} ON TABLES FROM {_ROLE_APPLICATION}"
    )

    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")
