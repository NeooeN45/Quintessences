"""Méta-test — migration pgvector (20260731_0024).

Vérifie que la migration :
1. Déclare le bon head (revises 20260728_0023).
2. Crée l'extension vector de manière idempotente.
3. Ajoute la colonne embedding sur entity.
4. Crée l'index IVFFlat pour la recherche cosinus.
5. Le downgrade supprime colonne et index (mais pas l'extension).

Ce test ne nécessite pas de base de données : il inspecte le code
source de la migration (AST + inspection des chaînes SQL).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260731_0024_pgvector_embeddings.py"
)


def _load_migration_module():
    """Charge le module de migration sans exécuter upgrade/downgrade."""
    spec = importlib.util.spec_from_file_location("migration_0024", _MIGRATION_PATH)
    assert spec is not None, f"Impossible de charger {_MIGRATION_PATH}"
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def migration():
    """Module de migration chargé une fois."""
    return _load_migration_module()


def test_migration_file_exists() -> None:
    """Le fichier de migration doit exister."""
    assert _MIGRATION_PATH.exists(), f"Migration manquante : {_MIGRATION_PATH}"


def test_revision_id_is_correct(migration) -> None:
    """L'identifiant de révision doit être 20260731_0024."""
    assert migration.revision == "20260731_0024"


def test_down_revision_chains_to_previous_head(migration) -> None:
    """La migration doit chaîner sur le head précédent (20260728_0023)."""
    assert migration.down_revision == "20260728_0023"


def test_upgrade_creates_vector_extension(migration) -> None:
    """upgrade() doit créer l'extension vector de manière idempotente."""
    import inspect

    source = inspect.getsource(migration.upgrade)
    assert (
        "CREATE EXTENSION IF NOT EXISTS vector" in source
    ), "L'extension pgvector doit être créée avec IF NOT EXISTS pour l'idempotence"


def test_upgrade_adds_embedding_column(migration) -> None:
    """upgrade() doit ajouter la colonne embedding sur entity."""
    import inspect

    source = inspect.getsource(migration.upgrade)
    assert (
        "ADD COLUMN IF NOT EXISTS embedding" in source
    ), "La colonne embedding doit être ajoutée avec IF NOT EXISTS"
    assert "vector(" in source, "La colonne doit utiliser le type vector(N)"


def test_upgrade_creates_ivfflat_index(migration) -> None:
    """upgrade() doit créer un index IVFFlat pour la recherche cosinus."""
    import inspect

    source = inspect.getsource(migration.upgrade)
    assert "ivfflat" in source.lower(), "L'index doit être de type ivfflat"
    assert "vector_cosine_ops" in source, "L'opclass doit être vector_cosine_ops"
    assert "IF NOT EXISTS" in source, "L'index doit être créé avec IF NOT EXISTS"


def test_downgrade_drops_index_and_column(migration) -> None:
    """downgrade() doit supprimer l'index et la colonne (réversibilité)."""
    import inspect

    source = inspect.getsource(migration.downgrade)
    assert "DROP INDEX IF EXISTS ix_entity_embedding" in source
    assert "DROP COLUMN IF EXISTS embedding" in source


def test_downgrade_preserves_extension(migration) -> None:
    """downgrade() ne doit PAS supprimer l'extension (choix d'infrastructure)."""
    import inspect

    source = inspect.getsource(migration.downgrade)
    assert "DROP EXTENSION" not in source, (
        "L'extension pgvector ne doit pas être supprimée au downgrade — "
        "c'est un choix d'infrastructure, pas une décision métier"
    )


def test_embedding_dimension_is_1536(migration) -> None:
    """La dimension des embeddings doit être 1536 (text-embedding-3-small)."""
    assert migration._EMBEDDING_DIMENSION == 1536
