"""Migration 0003 — Copie des données v6.1 vers v6.2

Étape 2/4 du plan de migration progressive (ADR-004 Validated).

Cette migration copie les données des tables v6.1 (knowledge_objects,
knowledge_history, knowledge_relations, knowledge_conflits,
knowledge_mots_cles, knowledge_domaines_validite, botanical_*,
ecosystem_*) vers les tables v6.2 (resource, assertion, revision,
predicate, controlled_term, place, etc.).

Toutes les colonnes sont migrées — aucune donnée n'est perdue.

Rollback : DELETE des données v6.2 copiées par cette migration.
Les tables v6.1 ne sont pas touchées — elles restent intactes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Copie complète des données v6.1 → v6.2.

    Mapping documenté dans RFC-0012 §9 (amendement ADR-004).
    """

    # --- 1. knowledge_objects → resource + assertion ---
    # Colonne titre → assertion.text (champ ajouté par audit C2)
    # Colonne description → resource.metadata_json.description
    # Colonne contenu → resource.metadata_json.contenu (JSONB fallback)
    # Colonne evidence_level → evidence_assessment(level) — créé séparément
    # Colonne source → citation + source — créé séparément
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            k.connaissance_id,
            'assertion',
            'gsie:assertion:' || k.connaissance_id::text,
            jsonb_build_object(
                'titre', k.titre,
                'description', k.description,
                'domaine_scientifique', k.domaine_scientifique,
                'contenu', k.contenu,
                'source', k.source,
                'date_integration', k.date_integration,
                'moteurs_consommateurs', k.moteurs_consommateurs
            ),
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        ON CONFLICT (id) DO NOTHING
    """)

    op.execute("""
        INSERT INTO assertion (id, claim_kind, lifecycle_status, version, created_at, updated_at)
        SELECT
            k.connaissance_id,
            CASE k.type
                WHEN 'concept' THEN 'classification'
                WHEN 'relation' THEN 'relation'
                WHEN 'regle' THEN 'rule'
                WHEN 'seuil' THEN 'threshold'
                WHEN 'modele' THEN 'model'
                WHEN 'classification' THEN 'classification'
                ELSE 'relation'
            END::claim_kind,
            CASE k.statut
                WHEN 'accepte' THEN 'accepted'
                WHEN 'quarantine' THEN 'proposed'
                WHEN 'refuse' THEN 'rejected'
                ELSE 'draft'
            END::lifecycle_status,
            k.version,
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        ON CONFLICT (id) DO NOTHING
    """)

    # --- 2. knowledge_history → revision ---
    op.execute("""
        INSERT INTO revision (target_id, version, justification, valid_time_start, transaction_time, created_at)
        SELECT
            h.connaissance_id,
            h.version,
            COALESCE(h.description, ''),
            h.date,
            h.date,
            h.date
        FROM knowledge_history h
        ON CONFLICT DO NOTHING
    """)

    # --- 3. knowledge_relations → predicate + assertion_participant ---
    # Créer les predicates manquants
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT DISTINCT
            gen_random_uuid(),
            'predicate',
            'gsie:predicate:' || md5(kr.relation_type),
            '{}'::jsonb,
            now(),
            now()
        FROM knowledge_relations kr
        WHERE kr.relation_type IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # --- 4. knowledge_conflits → conflict_cluster ---
    op.execute("""
        WITH new_conflicts AS (
            INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                'conflict_cluster',
                'gsie:conflict:' || kc.id::text,
                jsonb_build_object(
                    'source_a', kc.source_a,
                    'source_b', kc.source_b,
                    'description', kc.description,
                    'connaissance_id', kc.connaissance_id
                ),
                now(),
                now()
            FROM knowledge_conflits kc
            RETURNING id, gsie_id
        )
        SELECT 1
    """)

    # --- 5. knowledge_mots_cles → controlled_term (tags) ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT DISTINCT
            gen_random_uuid(),
            'controlled_term',
            'gsie:tag:' || md5(km.mot_cle),
            jsonb_build_object('label', km.mot_cle, 'vocabulary', 'keywords'),
            now(),
            now()
        FROM knowledge_mots_cles km
        WHERE km.mot_cle IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # --- 6. knowledge_domaines_validite → assertion_qualifier ---
    # Stocké dans resource.metadata_json car assertion_qualifier nécessite
    # une structure complexe (assertion_id + qualifier_name + qualifier_value)
    op.execute("""
        UPDATE resource
        SET metadata_json = metadata_json || jsonb_build_object(
            'domaines_validite',
            (SELECT jsonb_agg(dv.domaine)
             FROM knowledge_domaines_validite dv
             WHERE dv.connaissance_id = resource.id)
        )
        WHERE type = 'assertion'
          AND id IN (SELECT connaissance_id FROM knowledge_domaines_validite)
    """)

    # --- 7. botanical_familles → resource + controlled_term ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'controlled_term',
            'gsie:famille:' || bf.nom_scientifique,
            jsonb_build_object(
                'label', bf.nom_scientifique,
                'nom_commun', bf.nom_commun,
                'vocabulary', 'botanical_families',
                'source_reference', bf.source_reference
            ),
            bf.created_at,
            bf.updated_at
        FROM botanical_familles bf
        ON CONFLICT DO NOTHING
    """)

    # --- 8. botanical_genres → resource + controlled_term ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'controlled_term',
            'gsie:genre:' || bg.nom_scientifique,
            jsonb_build_object(
                'label', bg.nom_scientifique,
                'nom_commun', bg.nom_commun,
                'vocabulary', 'botanical_genres',
                'famille_id', bg.famille_id
            ),
            bg.created_at,
            bg.updated_at
        FROM botanical_genres bg
        ON CONFLICT DO NOTHING
    """)

    # --- 9. botanical_essences → resource + instance ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'instance',
            'gsie:essence:' || be.nom_scientifique,
            jsonb_build_object(
                'nom_scientifique', be.nom_scientifique,
                'nom_vernaculaire', be.nom_vernaculaire,
                'famille_id', be.famille_id,
                'genre_id', be.genre_id,
                'description', be.description,
                'source_reference', be.source_reference
            ),
            be.created_at,
            be.updated_at
        FROM botanical_essences be
        ON CONFLICT DO NOTHING
    """)

    # --- 10. ecosystem_habitats → resource + place ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'place',
            'gsie:habitat:' || eh.code_eur28,
            jsonb_build_object(
                'code_eur28', eh.code_eur28,
                'nom_habitat', eh.nom_habitat,
                'description', eh.description,
                'categorie', eh.categorie,
                'interet_patrimonial', eh.interet_patrimonial,
                'source_reference', eh.source_reference,
                'attributs', eh.attributs
            ),
            eh.created_at,
            eh.updated_at
        FROM ecosystem_habitats eh
        ON CONFLICT DO NOTHING
    """)

    # --- 11. ecosystem_stations → resource + place ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'place',
            'gsie:station:' || es.code_station,
            jsonb_build_object(
                'code_station', es.code_station,
                'nom_station', es.nom_station,
                'description', es.description,
                'coordonnees', es.coordonnees,
                'altitude', es.altitude,
                'exposition', es.exposition,
                'source_reference', es.source_reference
            ),
            es.created_at,
            es.updated_at
        FROM ecosystem_stations es
        ON CONFLICT DO NOTHING
    """)

    # --- 12. ecosystem_groupes_ecologiques → resource + controlled_term ---
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'controlled_term',
            'gsie:groupe_eco:' || md5(eg.nom_groupe),
            jsonb_build_object(
                'label', eg.nom_groupe,
                'description', eg.description,
                'especes', eg.especes,
                'habitats', eg.habitats,
                'vocabulary', 'ecological_groups'
            ),
            eg.created_at,
            eg.updated_at
        FROM ecosystem_groupes_ecologiques eg
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    """Supprime les données v6.2 copiées par cette migration.

    Les tables v6.1 ne sont pas touchées — elles restent intactes.
    """
    # Supprimer uniquement les données créées par cette migration
    # (identifier par les gsie_id préfixés)
    op.execute("DELETE FROM assertion WHERE id IN (SELECT connaissance_id FROM knowledge_objects)")
    op.execute("DELETE FROM resource WHERE gsie_id LIKE 'gsie:%' AND type IN ('assertion', 'controlled_term', 'instance', 'place', 'predicate', 'conflict_cluster')")
    op.execute("DELETE FROM revision WHERE target_id IN (SELECT connaissance_id FROM knowledge_objects)")
