"""Index d'idempotence + tables d'enrichissement (image, description, progression).

Cette migration adresse les constats P1 de l'audit qualité base du
2026-08-01 et prépare la scalabilité du pipeline Treekipedia vers
67 927 espèces :

1. **Index unique composite sur `entity_alias(namespace, external_id)`**
   (P1-1) : le lookup d'idempotence faisait un Seq Scan à chaque ingestion.
   L'index unique accélère le lookup ET ajoute une contrainte DB
   d'unicité (aujourd'hui uniquement applicative).

2. **Index GIN sur `resource.metadata_json`** (P1-2) : accélère les
   recherches par clé JSONB (taxonomy, primary_image, wikipedia_extract).

3. **Table `entity_image`** (P3-1) : stocke les images Wikimedia dans une
   table dédiée plutôt que dans `metadata_json`. Permet multi-images,
   validation de URLs, requêtes SQL natives, index sur `entity_id`.

4. **Table `entity_description`** (P3-2) : descriptions multilingues
   (Wikipédia EN/FR, etc.) dans une table dédiée. Remplace
   `metadata_json->wikipedia_extract`.

5. **Table `ingestion_progress`** (P1-3) : checkpoint de progression pour
   reprise automatique après crash du pipeline d'ingestion.

6. **COMMENT ON COLUMN** (P3-3) : data dictionary sur les tables
   centrales (resource, entity_alias, entity) et les nouvelles tables.

Réversibilité : index et tables sont supprimés au downgrade. Les
données d'enrichissement déjà présentes dans `metadata_json` ne sont
pas migrées automatiquement (script `migrate_enrichment_to_tables.py`
à part pour ne pas surcharger cette migration).

Revision ID: 20260801_0027
Revises: 20260801_0026
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0027"
down_revision: str | None = "20260801_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _refuser_les_doublons_d_alias() -> None:
    """Arrête la migration sur un diagnostic lisible plutôt qu'une erreur brute.

    L'unicité de `(namespace, external_id)` n'était jusqu'ici qu'applicative :
    rien ne garantit que la base n'en porte pas déjà un doublon. Sans ce
    contrôle, `CREATE UNIQUE INDEX` échoue avec le message du pilote — qui
    nomme une seule paire fautive et n'indique ni combien il y en a, ni quoi
    faire. Le déploiement s'arrête alors sans que l'exploitant sache si le
    problème tient à une ligne ou à dix mille.
    """
    doublons = (
        op.get_bind()
        .execute(
            sa.text(
                """
            SELECT namespace, external_id, count(*) AS occurrences
            FROM entity_alias
            GROUP BY namespace, external_id
            HAVING count(*) > 1
            ORDER BY occurrences DESC
            LIMIT 5
            """
            )
        )
        .fetchall()
    )
    if not doublons:
        return

    total = (
        op.get_bind()
        .execute(
            sa.text(
                """
            SELECT count(*) FROM (
                SELECT 1 FROM entity_alias
                GROUP BY namespace, external_id HAVING count(*) > 1
            ) AS d
            """
            )
        )
        .scalar_one()
    )
    echantillon = ", ".join(f"{ns}/{ext} ×{n}" for ns, ext, n in doublons)
    raise RuntimeError(
        f"entity_alias porte {total} paire(s) (namespace, external_id) en "
        f"double : l'index unique idx_entity_alias_ns_extid ne peut pas etre "
        f"pose. Echantillon : {echantillon}. Dedoublonnez avant de rejouer "
        f"cette migration — la fusion releve du metier, pas d'un DELETE "
        f"automatique (CON-010)."
    )


def upgrade() -> None:
    # 1. Index unique composite sur entity_alias(namespace, external_id)
    # Résout P1-1 : Seq Scan → Index Scan unique + contrainte DB d'unicité.
    #
    # Le contrôle précède la pose : à 67 927 espèces, un échec de migration
    # sans diagnostic coûte plus cher que la requête d'agrégation.
    _refuser_les_doublons_d_alias()
    # Pose sans CONCURRENTLY, délibérément : la migration crée aussi trois
    # tables, et CONCURRENTLY exige de sortir de la transaction — un échec en
    # cours laisserait alors la base à moitié migrée, et l'index en état
    # INVALID. Le verrou en écriture sur `entity_alias` est tenable au volume
    # actuel. À revoir si la table doit être indexée base ouverte : il faudra
    # alors une migration dédiée, en `autocommit_block`.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_alias_ns_extid "
        "ON entity_alias (namespace, external_id)"
    )

    # 2. Index GIN sur resource.metadata_json (jsonb_path_ops = plus compact)
    # Résout P1-2 : recherche par clé JSONB accélérée.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_resource_metadata_gin "
        "ON resource USING GIN (metadata_json jsonb_path_ops)"
    )

    # 3. Table entity_image — images d'espèces (Wikimedia, etc.)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS entity_image (
            id              uuid PRIMARY KEY,
            entity_id       uuid NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
            url             varchar(1000) NOT NULL,
            license         varchar(200),
            photographer     varchar(300),
            page_url        varchar(1000),
            source          varchar(100) NOT NULL DEFAULT 'Wikimedia Commons',
            is_primary      boolean NOT NULL DEFAULT false,
            validated_at    timestamptz,
            last_checked_at timestamptz,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_entity_image_entity_id " "ON entity_image (entity_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_image_entity_primary "
        "ON entity_image (entity_id) WHERE is_primary = true"
    )

    # 4. Table entity_description — descriptions multilingues
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS entity_description (
            id          uuid PRIMARY KEY,
            entity_id   uuid NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
            language    varchar(10) NOT NULL,
            source      varchar(100) NOT NULL,
            content     text NOT NULL,
            quality     varchar(20),
            created_at  timestamptz NOT NULL DEFAULT now(),
            updated_at  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_entity_description_entity_id "
        "ON entity_description (entity_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_description_entity_lang_src "
        "ON entity_description (entity_id, language, source)"
    )

    # 5. Table ingestion_progress — checkpoint de progression pipeline
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_progress (
            id           uuid PRIMARY KEY,
            pipeline     varchar(100) NOT NULL UNIQUE,
            last_offset  integer NOT NULL DEFAULT 0,
            total        integer NOT NULL DEFAULT 0,
            status       varchar(20) NOT NULL DEFAULT 'pending',
            started_at   timestamptz,
            updated_at   timestamptz NOT NULL DEFAULT now(),
            metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )

    # 6. Data dictionary — COMMENT ON COLUMN sur les tables centrales
    _add_comments()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion_progress")
    op.execute("DROP INDEX IF EXISTS idx_entity_description_entity_lang_src")
    op.execute("DROP INDEX IF EXISTS idx_entity_description_entity_id")
    op.execute("DROP TABLE IF EXISTS entity_description")
    op.execute("DROP INDEX IF EXISTS idx_entity_image_entity_primary")
    op.execute("DROP INDEX IF EXISTS idx_entity_image_entity_id")
    op.execute("DROP TABLE IF EXISTS entity_image")
    op.execute("DROP INDEX IF EXISTS idx_resource_metadata_gin")
    op.execute("DROP INDEX IF EXISTS idx_entity_alias_ns_extid")
    # Les COMMENT sont laissés : ils ne gênent pas et documentent l'intention.


def _add_comments() -> None:
    """Data dictionary — documente les colonnes des tables centrales."""
    comments = [
        # resource
        ("resource", "id", "Identifiant UUID de la ressource (PK)."),
        (
            "resource",
            "type",
            "Type de ressource (entity, assertion, observation, entity_alias, etc.).",
        ),
        (
            "resource",
            "gsie_id",
            "Identifiant GSIE déterministe (ex : gsie:entity:taxon:2685484). Unique.",
        ),
        (
            "resource",
            "metadata_json",
            "Métadonnées JSONB (taxonomy, primary_image, wikipedia_extract, common_names).",
        ),
        ("resource", "deleted_at", "Soft delete (CON-010) — jamais DELETE physique."),
        # entity_alias
        ("entity_alias", "entity_id", "FK vers l'entity référencée par cet alias."),
        ("entity_alias", "namespace", "Référentiel externe (gbif, treekipedia, inpn, taxref)."),
        (
            "entity_alias",
            "external_id",
            "Identifiant dans le référentiel externe (ex : 2685484 pour GBIF).",
        ),
        ("entity_alias", "external_url", "URL optionnelle vers la page du référentiel externe."),
        # entity
        ("entity", "entity_subtype", "Sous-type d'entity (taxon, concept, instance, etc.)."),
        (
            "entity",
            "embedding",
            "Embedding sémantique 1536-dim (text-embedding-3-small). Nullable.",
        ),
        # entity_image
        ("entity_image", "entity_id", "FK vers l'entity (taxon) représentée par cette image."),
        ("entity_image", "url", "URL de l'image (Wikimedia Commons, etc.)."),
        ("entity_image", "license", "License de l'image (ex : CC-BY-SA-3.0)."),
        ("entity_image", "photographer", "Auteur/photographe de l'image."),
        ("entity_image", "is_primary", "Image principale de l'entity (une seule par entity)."),
        (
            "entity_image",
            "validated_at",
            "Date de dernière validation de l'URL (null = non validée).",
        ),
        (
            "entity_image",
            "last_checked_at",
            "Date du dernier check de l'URL (null = jamais vérifiée).",
        ),
        # entity_description
        ("entity_description", "entity_id", "FK vers l'entity décrite."),
        ("entity_description", "language", "Code langue ISO 639-1 (en, fr, de, etc.)."),
        ("entity_description", "source", "Source de la description (wikipedia, trenkia, etc.)."),
        (
            "entity_description",
            "content",
            "Texte de la description (extrait introductif Wikipédia).",
        ),
        ("entity_description", "quality", "Qualité estimée (high, medium, low, stub)."),
        # ingestion_progress
        (
            "ingestion_progress",
            "pipeline",
            "Nom du pipeline (treekipedia_ingest, treekipedia_enrich).",
        ),
        ("ingestion_progress", "last_offset", "Dernier offset traité avec succès."),
        ("ingestion_progress", "total", "Nombre total d'éléments à traiter."),
        (
            "ingestion_progress",
            "status",
            "Statut (pending, running, completed, failed, interrupted).",
        ),
    ]
    for table, column, comment in comments:
        op.execute(
            f"COMMENT ON COLUMN {table}.{column} IS '{comment.replace(chr(39), chr(39) + chr(39))}'"
        )
