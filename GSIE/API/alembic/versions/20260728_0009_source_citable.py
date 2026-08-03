"""Une source enregistree doit etre citable : auteur et date (CON-005).

`SourceReference` — le format qu'attend toute conclusion pour citer — exige
`type_source`, `auteur` et `reference`. Or la table `source` ne portait ni
auteur ni date de publication : une source enregistree en base ne pouvait donc
pas produire une citation complete.

Consequence concrete : toutes les `SourceReference` du code sont aujourd'hui
des constantes ecrites en dur dans les moteurs. Aucune n'est construite depuis
la base. Une regle recuperee depuis le Knowledge Engine n'aurait donc pas pu
citer sa source, alors que DEC-000038 exige qu'une regle non sourcee ne sorte
pas.

Colonnes NULLABLE : les lignes anterieures a cette revision n'ont pas d'auteur,
et leur en inventer un serait exactement la faute que ADR-009 previent.
L'exigence porte a l'ecriture, via la porte de validation — meme schema que
`autecology_profile.territory_description` et
`silvicultural_rule.validity_zone_description`.

Revision ID: 20260728_0009
Revises: 20260728_0008
Create Date: 2026-07-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0009"
down_revision: str | None = "20260728_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "source"
_COLONNES: tuple[tuple[str, str, str], ...] = (
    (
        "auteur",
        "VARCHAR(500)",
        "Auteurs de la source, sous la forme attendue pour une citation",
    ),
    (
        "date_publication",
        "VARCHAR(50)",
        "Date de publication declaree par la source (annee ou date complete)",
    ),
)


def upgrade() -> None:
    for colonne, type_sql, commentaire in _COLONNES:
        op.execute(f"ALTER TABLE {_TABLE} ADD COLUMN {colonne} {type_sql}")
        op.execute(f"COMMENT ON COLUMN {_TABLE}.{colonne} IS '{commentaire}'")


def downgrade() -> None:
    for colonne, _type_sql, _commentaire in _COLONNES:
        op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN {colonne}")
