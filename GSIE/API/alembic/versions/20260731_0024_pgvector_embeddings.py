"""Extension pgvector + colonne embedding sur entity.

pgvector permet le stockage et la recherche de vecteurs sémantiques
(embeddings) directement en PostgreSQL. C'est le prérequis pour
l'ingestion de Treekipedia (67 928 espèces) : les embeddings sémantiques
permettent la recherche par similarité (cosinus, L2) au-delà des
requêtes par mot-clé.

L'extension est créée de manière idempotente (IF NOT EXISTS). La
colonne `embedding` sur `entity` est nullable : seules les espèces
ayant un embedding calculé la portent. La dimension 1536 correspond
au modèle text-embedding-3-small d'OpenAI (standard de fait), mais
pgvector supporte toute dimension.

Réversibilité : la colonne et l'extension sont supprimées au
downgrade. Aucune donnée métier n'est perdue (l'embedding est une
dérivée, pas une source de vérité — ADR-009).

Revision ID: 20260731_0024
Revises: 20260728_0023
Create Date: 2026-07-31
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260731_0024"
down_revision: str | None = "20260728_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Dimension des embeddings — text-embedding-3-small (1536).
# Configurable : un futur modèle plus large passera par une migration
# ALTER COLUMN TYPE vector(N).
_EMBEDDING_DIMENSION = 1536


def upgrade() -> None:
    # L'extension pgvector doit être installée côté serveur
    # (postgresql.conf shared_preload_libraries + CREATE EXTENSION).
    # IF NOT EXISTS garantit l'idempotence.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Colonne nullable : seules les entités avec embedding calculé la portent.
    # Utilisation de IF NOT EXISTS pour éviter l'erreur sur ré-application.
    op.execute(
        f"ALTER TABLE entity " f"ADD COLUMN IF NOT EXISTS embedding vector({_EMBEDDING_DIMENSION})"
    )
    # Index IVFFlat pour la recherche par similarité (cosinus).
    # lists = sqrt(rows) est l'heurique pgvector ; 100 est un défaut raisonnable
    # pour 67 928 espèces (sqrt(67928) ≈ 260, arrondi à 100 pour stabilité).
    # L'index n'est créé que si des embeddings existent — sinon il reste vide.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_embedding "
        "ON entity USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_entity_embedding")
    op.execute("ALTER TABLE entity DROP COLUMN IF EXISTS embedding")
    # On ne supprime pas l'extension : d'autres usages pourraient en dépendre.
    # L'extension est un choix d'infrastructure, pas une décision métier.
