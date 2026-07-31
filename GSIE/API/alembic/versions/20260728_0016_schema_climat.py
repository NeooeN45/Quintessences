"""Schema de domaine gsie_climat — RFC-0029 §4.1, GSIE-PROMPT-0027.

Quatrieme des sept schemas de domaine. Le climat n'a pas encore de table
dediee dans le metamodele v6.2 : les observations climatiques vivent dans
les tables transverses (`observation`, `phenomenon`, `scenario`). Le
schema est cree vide, pret a recevoir les tables climatiques futures
(stations, normales, indices, scénarios DRIAS).

`gsie_application` recoit USAGE sur le schema et SELECT/INSERT/UPDATE sur
les tables futures (ALTER DEFAULT PRIVILEGES) — jamais DELETE (CON-010).
Le schema etant vide, il n'y a pas de table existante a doter.

Revision ID: 20260728_0016
Revises: 20260728_0015
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0016"
down_revision: str | None = "20260728_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_climat"
_ROLE_APPLICATION = "gsie_application"
_ECRITURE = "SELECT, INSERT, UPDATE"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    # Le schema est vide : pas de table existante a doter. Les droits par defaut
    # s'appliqueront aux tables climatiques futures.
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"GRANT {_ECRITURE} ON TABLES TO {_ROLE_APPLICATION}"
    )

    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA} IS "
        "'Domaine climat : stations, normales, indices, scenarios. "
        "RFC-0029 §4.1. Schema vide en v6.2 — tables futures.'"
    )


def downgrade() -> None:
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"REVOKE {_ECRITURE} ON TABLES FROM {_ROLE_APPLICATION}"
    )

    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")
