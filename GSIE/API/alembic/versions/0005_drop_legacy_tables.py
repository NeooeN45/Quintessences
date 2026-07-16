"""Migration 0005 — Suppression des anciennes tables v6.1

Étape 4/4 du plan de migration progressive (ADR-004 Validated).

⚠️ Cette migration est IRRÉVERSIBLE. Elle supprime définitivement les
tables v6.1 (knowledge_objects, knowledge_history, knowledge_relations,
knowledge_conflits, knowledge_mots_cles, knowledge_domaines_validite,
botanical_familles, botanical_genres, botanical_essences,
ecosystem_habitats, ecosystem_stations, ecosystem_groupes_ecologiques).

Ne l'exécuter qu'après :
1. Validation complète que les données v6.2 sont correctes (migration 0003)
2. Validation que les moteurs fonctionnent sur le schéma v6.2 (migration 0004)
3. Backup complet de la base

Rollback : IMPOSSIBLE — restaurer depuis backup.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tables v6.1 à supprimer (ordre inverse des dépendances)
_LEGACY_TABLES = [
    "knowledge_mots_cles",
    "knowledge_domaines_validite",
    "knowledge_conflits",
    "knowledge_relations",
    "knowledge_history",
    "knowledge_objects",
    "ecosystem_groupes_ecologiques",
    "ecosystem_stations",
    "ecosystem_habitats",
    "botanical_essences",
    "botanical_genres",
    "botanical_familles",
]


def upgrade() -> None:
    """Suppression définitive des tables v6.1.

    ⚠️ IRRÉVERSIBLE — s'assurer qu'un backup existe avant d'exécuter.
    """
    for table in _LEGACY_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


def downgrade() -> None:
    """Impossible — les tables v6.1 sont supprimées définitivement.

    Restaurer depuis backup si nécessaire.
    """
    raise NotImplementedError(
        "downgrade() non disponible pour la migration 0005 — "
        "les tables v6.1 sont supprimées définitivement. "
        "Restaurer depuis backup si nécessaire."
    )
