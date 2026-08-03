"""Six descriptions de colonnes deviennent visibles en base (`doc=` -> `comment=`).

`doc=` est de la documentation Python : SQLAlchemy la garde en memoire et
PostgreSQL ne la voit jamais. Six colonnes portaient donc une description
qu'aucune lecture du schema ne montrait — ni la commande de description de
table de psql, ni un outil de modelisation, ni la personne qui reprend la base
sans lire le code Python.

Pour un systeme dont le produit est la connaissance, une description invisible
dans le schema n'est pas une description. Le cas est deja tranche pour
`silvicultural_rule.validity_zone_description` et `models_ai` : `comment=`, et
un `COMMENT ON COLUMN` dans la migration.

`silvicultural_rule.human_validator` est la plus consequente : son texte porte
une contrainte metier — « obligatoire des que status passe a accepted » — que
seul le code Python enoncait.

Aucune donnee n'est touchee : un commentaire est une metadonnee de catalogue.

Revision ID: 20260728_0010
Revises: 20260728_0009
Create Date: 2026-07-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0010"
down_revision: str | None = "20260728_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, colonne, commentaire) — textes identiques a `comment=` dans les
# modeles. Le controle de derive strict de
# `tests/integration/test_migration_baseline.py` echoue au moindre ecart, y
# compris une apostrophe ou un tiret different.
_COLONNES: tuple[tuple[str, str, str], ...] = (
    ("diagnostic", "contenu", "Diagnostic sérialisé intégral — seule source de relecture"),
    (
        "station_type",
        "validity_zone_description",
        "Zone de validité du guide en texte libre (pas de géométrie en tranche 2)",
    ),
    (
        "station_observation",
        "key_path_followed",
        "Réponses saisies et embranchement obtenu dans la clé du guide",
    ),
    (
        "silvicultural_rule",
        "human_validator",
        "Nom/qualité du validateur humain (curateur + forestier compétent) — obligatoire dès que status passe à accepted",
    ),
    (
        "provenance_material",
        "base_material",
        "Identifiant du matériel de base (verger à graines, peuplement classé, etc.)",
    ),
    (
        "provenance_material",
        "decree_version",
        "Version de l'arrêté MFR qui fonde l'admissibilité (ex. « arrêté du 6 mars 2026 »)",
    ),
)


def _echapper(texte: str) -> str:
    """Double les apostrophes — un `COMMENT ON` n'accepte pas de parametre lie.

    Deux de ces textes en contiennent (« l'arrete », « l'admissibilite ») et une
    apostrophe non echappee ferme la chaine SQL : `PostgresSyntaxError` a la
    migration, faute deja commise dans ce depot.
    """
    return texte.replace("'", "''")


def upgrade() -> None:
    for table, colonne, commentaire in _COLONNES:
        op.execute(f"COMMENT ON COLUMN {table}.{colonne} IS '{_echapper(commentaire)}'")


def downgrade() -> None:
    for table, colonne, _commentaire in _COLONNES:
        op.execute(f"COMMENT ON COLUMN {table}.{colonne} IS NULL")
