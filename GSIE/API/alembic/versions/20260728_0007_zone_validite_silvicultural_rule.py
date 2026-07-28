"""Zone de validite geographique sur silvicultural_rule (DEC-000038).

DEC-000038 exige qu'une regle declare son domaine de validite : un domaine non
renseigne vaut « nulle part », jamais « partout ». Une regle tiree d'un
catalogue de stations regional, appliquee hors de sa zone, produirait une
conclusion fausse citant une source reelle, avec une chaine d'inference
complete et un niveau de preuve intact — invisible.

Or `silvicultural_rule` ne portait AUCUNE colonne de territoire.
`required_context` decrit un contexte sylvicole (« futaie reguliere de
hetre »), pas une zone geographique : les deux ne sont pas interchangeables.

La colonne est ajoutee en NULLABLE. Motif : les lignes anterieures a la
decision n'ont pas de zone, et leur en inventer une serait exactement la faute
que DEC-000038 previent. L'exigence est portee par la porte de validation a
l'ecriture, comme pour `autecology_profile.territory_description`. Les lignes
anciennes restent donc lisibles et identifiables comme non qualifiees, plutot
que faussement qualifiees.

Revision ID: 20260728_0007
Revises: 20260728_0006
Create Date: 2026-07-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0007"
down_revision: str | None = "20260728_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "silvicultural_rule"
_COLONNE = "validity_zone_description"


def upgrade() -> None:
    op.execute(f"ALTER TABLE {_TABLE} ADD COLUMN {_COLONNE} TEXT")
    op.execute(
        f"COMMENT ON COLUMN {_TABLE}.{_COLONNE} IS "
        "'Zone geographique de validite declaree par la source (DEC-000038)'"
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN {_COLONNE}")
