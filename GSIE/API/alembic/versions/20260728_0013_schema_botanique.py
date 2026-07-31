"""Schema de domaine gsie_botanique — RFC-0029 §4.1, GSIE-PROMPT-0027.

Premier des sept schemas de domaine prevus par `RFC-0029`. La botanique
est le domaine le moins dependant des autres : ses tables reference
`resource` (noyau) et `entity` (taxons), mais aucune table d'un autre
domaine.

Six tables quittent `public` pour `gsie_botanique` :

| Table | Module | Raison |
|---|---|---|
| `autecology_profile` | forestry | Observation autecologique pour un taxon |
| `trait_definition` | ecology | Definition d'un trait fonctionnel (Leaf Area, SLA…) |
| `trait_value` | ecology | Valeur d'un trait pour une entite (taxon) |
| `botanical_identification_request` | identification | Capture terrain pour identification Pl@ntNet |
| `botanical_identification_result` | identification | Reponse brute d'un fournisseur d'identification |
| `botanical_identification_decision` | identification | Decision humaine sur un resultat d'identification |

`resource` reste dans `public` (GSIE-PROMPT-0027 §1) : 97 % des cles
etrangeres pointent vers lui, et le renommer n'apporte aucune securite.
Les cles etrangeres traversent les schemas : `ALTER TABLE SET SCHEMA`
preserve les contraintes, verifie sur cette base avant d'ecrire cette
migration.

**Renommage des index.** `ALTER TABLE SET SCHEMA` deplace les index vers
le nouveau schema mais conserve leur nom (`ix_<table>_<colonne>`).
SQLAlchemy, quand une table porte un `schema`, genere un nom prefixe :
`ix_<schema>_<table>_<colonne>`. Sans renommage explicite, le controle
de derive detecte l'ecart et echoue. Chaque index est donc renomme
apres le deplacement.

`gsie_application` recoit `SELECT, INSERT, UPDATE` sur le schema — jamais
`DELETE` (CON-010). Le refus devient structurel : une suppression ecrite
par erreur echoue au lieu de detruire.

Revision ID: 20260728_0013
Revises: 20260728_0012
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0013"
down_revision: str | None = "20260728_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_botanique"
_TABLES = (
    "autecology_profile",
    "trait_definition",
    "trait_value",
    "botanical_identification_request",
    "botanical_identification_result",
    "botanical_identification_decision",
)

# Colonnes portant un index implicite (`mapped_column(..., index=True)`) pour
# chaque table deplacee. SQLAlchemy nomme ces index `ix_<schema>_<table>_<col>`
# quand la table a un schema ; la base les nomme `ix_<table>_<col>` avant le
# deplacement. La migration renomme chaque index apres `SET SCHEMA` pour
# reconcilier les deux conventions.
_INDEXED_COLUMNS: dict[str, tuple[str, ...]] = {
    "autecology_profile": ("variable", "source_id", "species_entity_id"),
    "trait_definition": ("unit_id", "name"),
    "trait_value": (
        "entity_id",
        "observation_id",
        "uncertainty_id",
        "trait_definition_id",
        "value_term_id",
        "scale_context_id",
        "unit_id",
    ),
    "botanical_identification_request": ("parcel_id", "requested_by_id"),
    "botanical_identification_result": ("request_id",),
    "botanical_identification_decision": (
        "result_id",
        "validated_by_id",
        "manual_species_entity_id",
    ),
}

_ROLE_APPLICATION = "gsie_application"
_ECRITURE = "SELECT, INSERT, UPDATE"


def _renommer_index(table: str, colonne: str, nouveau_schema: str) -> None:
    """Renomme un index de `ix_<table>_<col>` vers `ix_<schema>_<table>_<col>`."""
    ancien = f"ix_{table}_{colonne}"
    nouveau = f"ix_{nouveau_schema}_{table}_{colonne}"
    op.execute(f"ALTER INDEX {nouveau_schema}.{ancien} RENAME TO {nouveau}")


def _restaurer_index(table: str, colonne: str, ancien_schema: str) -> None:
    """Renomme un index de `ix_<schema>_<table>_<col>` vers `ix_<table>_<col>`."""
    ancien = f"ix_{ancien_schema}_{table}_{colonne}"
    nouveau = f"ix_{table}_{colonne}"
    op.execute(f"ALTER INDEX {ancien_schema}.{ancien} RENAME TO {nouveau}")


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    for table in _TABLES:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA {_SCHEMA}")

    # Reconcilier les noms d'index avec la convention SQLAlchemy prefixee.
    for table, colonnes in _INDEXED_COLUMNS.items():
        for colonne in colonnes:
            _renommer_index(table, colonne, _SCHEMA)

    # Le role applicatif existe depuis 20260728_0012. On etend ses droits au
    # nouveau schema : lecture-ecriture sans DELETE (CON-010).
    op.execute(f"GRANT USAGE ON SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}")
    op.execute(
        f"GRANT {_ECRITURE} ON ALL TABLES IN SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}"
    )
    op.execute(
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {_SCHEMA} TO {_ROLE_APPLICATION}"
    )
    # Une table ajoutee plus tard doit heriter des memes droits, sinon
    # l'application perd l'acces au premier ajout sans que rien ne le signale.
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"GRANT {_ECRITURE} ON TABLES TO {_ROLE_APPLICATION}"
    )

    op.execute(
        f"COMMENT ON SCHEMA {_SCHEMA} IS "
        "'Domaine botanique : taxons, autecologie, identification. "
        "RFC-0029 §4.1.'"
    )


def downgrade() -> None:
    # Restaurer les noms d'index avant de deplacer les tables : apres SET SCHEMA
    # vers public, les index suivent mais conservent leur nom prefixe.
    for table, colonnes in _INDEXED_COLUMNS.items():
        for colonne in colonnes:
            _restaurer_index(table, colonne, _SCHEMA)

    for table in _TABLES:
        op.execute(f"ALTER TABLE {_SCHEMA}.{table} SET SCHEMA public")

    # Retirer les droits avant de supprimer le schema : sinon le DROP CASCADE
    # les supprime implicitement, mais le retrait explicite est lisible a
    # l'audit.
    op.execute(
        f"REVOKE {_ECRITURE} ON ALL TABLES IN SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}"
    )
    op.execute(f"REVOKE USAGE ON SCHEMA {_SCHEMA} FROM {_ROLE_APPLICATION}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {_SCHEMA} "
        f"REVOKE {_ECRITURE} ON TABLES FROM {_ROLE_APPLICATION}"
    )

    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")
