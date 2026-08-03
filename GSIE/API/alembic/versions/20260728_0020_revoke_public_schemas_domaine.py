"""REVOKE FROM PUBLIC sur les schemas de domaine — defense en profondeur.

Le contre-audit de GSIE-PROMPT-0027 a releve que les migrations 0013 a
0019 ne faisaient pas `REVOKE ALL ON SCHEMA ... FROM PUBLIC`, contrairement
a 0011 (RGPD) qui le fait explicitement.

PostgreSQL n'accorde rien a PUBLIC sur les nouveaux schemas par defaut,
mais c'est une **defense en profondeur manquante** : si un DBA accorde
plus tard des droits a PUBLIC (par exemple pour faciliter un ad-hoc), les
schemas de domaine seraient exposes sans garde. Le `REVOKE` explicite rend
le refus lisible a l'audit et resistant aux erreurs d'exploitation.

Les sept schemas de domaine sont : gsie_botanique, gsie_foret,
gsie_gouvernance, gsie_climat, gsie_pedologie, gsie_hydro, gsie_feu.

Revision ID: 20260728_0020
Revises: 20260728_0019
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0020"
down_revision: str | None = "20260728_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMAS = (
    "gsie_botanique",
    "gsie_foret",
    "gsie_gouvernance",
    "gsie_climat",
    "gsie_pedologie",
    "gsie_hydro",
    "gsie_feu",
)


def upgrade() -> None:
    for schema in _SCHEMAS:
        # Sans ce REVOKE, PUBLIC conserve ses droits et l'isolement ne vaut rien.
        op.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM PUBLIC")


def downgrade() -> None:
    # Pas de restauration : PUBLIC n'avait aucun droit avant 0020, et le
    # downgrade des migrations 0013-0019 supprime les schemas (DROP SCHEMA
    # CASCADE). Restaurer des droits a PUBLIC sur des schemas qui vont
    # disparaitre n'a pas de sens.
    pass
