"""Defauts d'horodatage figes -- ALTER COLUMN SET DEFAULT now().

La baseline grave `DEFAULT 'now()'` avec des quotes sur trois colonnes.
PostgreSQL evalue cette chaine **une seule fois**, a la creation de la table,
et la fige en constante litterale :

    revision.created_at -> '2026-07-27 23:26:26.797516+00'::timestamp with time zone

Consequence verifiee sur base migree : toutes les lignes inserees sans valeur
explicite portent la date de la migration, jamais celle de leur creation.

- `revision.created_at` : c'est l'horodatage d'audit du Temporal Engine. Une
  date fausse sur chaque revision contredit directement CON-010, qui exige
  que rien ne soit modifie sans trace datee.
- `outbox_event.created_at` : la jauge `gsie_outbox_oldest_pending_age_seconds`
  est calculee depuis cette colonne. L'age du backlog est donc faux et derive
  sans borne a mesure que la date de migration s'eloigne.
- `inbox_event.received_at` : defaut dormant (aucun site d'insertion
  aujourd'hui), corrige avant que l'Inbox ne soit branchee.

Les modeles SQLAlchemy declarent deja `server_default=func.now()` : c'est la
base existante qui doit etre rattrapee. `alembic check` ne comparant pas les
server_default, cette derive restait invisible au controle automatique.

Revision ID: 20260728_0006
Revises: 20260727_0005
Create Date: 2026-07-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0006"
down_revision: str | None = "20260727_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, colonne) -- les trois colonnes gravees avec un defaut litteral.
_COLONNES: tuple[tuple[str, str], ...] = (
    ("revision", "created_at"),
    ("outbox_event", "created_at"),
    ("inbox_event", "received_at"),
)


def upgrade() -> None:
    for table, colonne in _COLONNES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {colonne} SET DEFAULT now()")


def downgrade() -> None:
    # Retablir un defaut fige serait retablir un defaut faux. On retire donc
    # simplement le defaut : une insertion sans valeur explicite echouera
    # franchement (colonnes NOT NULL) au lieu d'ecrire une date mensongere.
    for table, colonne in _COLONNES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {colonne} DROP DEFAULT")
