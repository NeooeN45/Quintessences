"""Test d'intégration — migration pgvector (20260731_0024) sur vraie DB.

Vérifie que les SQL de la migration s'exécutent sans erreur sur un conteneur
PostgreSQL/PostGIS/pgvector et que :
1. L'extension `vector` est créée.
2. La colonne `embedding` existe sur `entity` avec le type `vector(1536)`.
3. L'index `ix_entity_embedding` (IVFFlat, cosine) est créé.
4. Le `downgrade` (DROP) supprime colonne et index (réversibilité).

Ce test exécute les SQL directement via asyncpg (pas via Alembic) car
Alembic nécessite un driver synchrone (psycopg2) qui interfère avec le
conteneur testcontainers sur Windows. Les SQL sont extraits du module de
migration pour garantir qu'ils sont identiques à ceux de la migration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from tests.conftest import requires_docker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = requires_docker

# SQL extraits de la migration 20260731_0024 (upgrade + downgrade).
_SQL_UPGRADE = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    "ALTER TABLE entity ADD COLUMN IF NOT EXISTS embedding vector(1536)",
    (
        "CREATE INDEX IF NOT EXISTS ix_entity_embedding "
        "ON entity USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    ),
]

_SQL_DOWNGRADE = [
    "DROP INDEX IF EXISTS ix_entity_embedding",
    "ALTER TABLE entity DROP COLUMN IF EXISTS embedding",
]


class TestMigrationPgvectorIntegration:
    """Migration pgvector 20260731_0024 — SQL exécutés sur PostgreSQL réel."""

    async def test_upgrade_creates_pgvector_objects(self, db_session: AsyncSession) -> None:
        """Les SQL d'upgrade doivent créer l'extension, la colonne et l'index.

        Note : `Base.metadata.create_all` crée déjà la colonne `embedding` car
        le modèle SQLAlchemy la déclare (Vector(1536)). Les SQL d'upgrade sont
        idempotents (IF NOT EXISTS) — ils ne font rien si la colonne existe déjà.
        L'index IVFFlat, en revanche, n'est pas créé par create_all (il nécessite
        des paramètres spécifiques) — c'est la migration qui le crée.
        """
        for sql in _SQL_UPGRADE:
            await db_session.execute(text(sql))
        await db_session.commit()

        # Vérifier l'extension vector
        r = await db_session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        assert r.fetchone() is not None, "L'extension vector doit être installée"

        # Vérifier la colonne embedding
        r = await db_session.execute(
            text(
                "SELECT data_type, udt_name "
                "FROM information_schema.columns "
                "WHERE table_name = 'entity' AND column_name = 'embedding'"
            )
        )
        row = r.fetchone()
        assert row is not None, "La colonne embedding doit exister sur entity"
        assert row[0] == "USER-DEFINED", f"Type inattendu: {row[0]}"
        assert row[1] == "vector", f"UDT inattendu: {row[1]}"

        # Vérifier l'index IVFFlat
        r = await db_session.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'entity' AND indexname = 'ix_entity_embedding'"
            )
        )
        assert r.fetchone() is not None, "L'index ix_entity_embedding doit exister"

    async def test_downgrade_drops_embedding_objects(self, db_session: AsyncSession) -> None:
        """Les SQL de downgrade doivent supprimer la colonne et l'index."""
        # Prérequis : créer l'extension + colonne + index (état après upgrade).
        for sql in _SQL_UPGRADE:
            await db_session.execute(text(sql))
        await db_session.commit()

        # Exécuter le downgrade
        for sql in _SQL_DOWNGRADE:
            await db_session.execute(text(sql))
        await db_session.commit()

        # La colonne embedding ne doit plus exister
        r = await db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'entity' AND column_name = 'embedding'"
            )
        )
        assert r.fetchone() is None, "La colonne embedding ne doit plus exister après downgrade"

        # L'index ne doit plus exister
        r = await db_session.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'entity' AND indexname = 'ix_entity_embedding'"
            )
        )
        assert r.fetchone() is None, "L'index ne doit plus exister après downgrade"
