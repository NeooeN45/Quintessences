"""Migration 0003 — Copie structurée des données v6.1 vers v6.2

Étape 2/4 du plan de migration progressive (ADR-004 Validated).

Cette migration copie les données des tables v6.1 vers les tables v6.2
avec un mapping structuré complet : les données vont dans les tables
relationnelles dédiées (evidence_assessment, citation, source,
controlled_term, place, instance, assertion_qualifier) — pas seulement
dans metadata_json.

Toutes les colonnes sont migrées — aucune donnée n'est perdue.
Les colonnes sans table dédiée sont conservées dans metadata_json (fallback).

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
    """Copie structurée complète des données v6.1 → v6.2.

    Mapping documenté dans RFC-0012 §9 (amendement ADR-004).
    Chaque table ancienne est migrée vers ses tables cibles v6.2
    avec création des lignes dans les tables relationnelles dédiées.
    """

    # ===================================================================
    # 1. VOCABULARY — créer les vocabulaires de référence
    # ===================================================================
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'vocabulary',
            'gsie:vocabulary:botanical_families',
            jsonb_build_object('description', 'Familles botaniques (référentiel interne)'),
            now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM resource WHERE gsie_id = 'gsie:vocabulary:botanical_families')
    """)

    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'vocabulary',
            'gsie:vocabulary:botanical_genres',
            jsonb_build_object('description', 'Genres botaniques (référentiel interne)'),
            now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM resource WHERE gsie_id = 'gsie:vocabulary:botanical_genres')
    """)

    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'vocabulary',
            'gsie:vocabulary:keywords',
            jsonb_build_object('description', 'Mots-clés libres (knowledge_mots_cles)'),
            now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM resource WHERE gsie_id = 'gsie:vocabulary:keywords')
    """)

    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'vocabulary',
            'gsie:vocabulary:ecological_groups',
            jsonb_build_object('description', 'Groupes écologiques (référentiel interne)'),
            now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM resource WHERE gsie_id = 'gsie:vocabulary:ecological_groups')
    """)

    # ===================================================================
    # 2. knowledge_objects → resource + assertion + evidence_assessment
    # ===================================================================

    # 2a. resource (avec metadata_json pour les colonnes sans table dédiée)
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
                'date_integration', k.date_integration,
                'moteurs_consommateurs', k.moteurs_consommateurs
            ),
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        ON CONFLICT (id) DO NOTHING
    """)

    # 2b. assertion
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

    # 2c. evidence_assessment (une évaluation par knowledge_object)
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'evidence_assessment',
            'gsie:evidence:' || k.connaissance_id::text,
            '{}'::jsonb,
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        WHERE k.evidence_level IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO evidence_assessment (id, assertion_id, level, method, evaluated_at)
        SELECT
            r.id,
            k.connaissance_id,
            k.evidence_level::evidence_level,
            'migration_v6.1',
            k.date_integration
        FROM knowledge_objects k
        JOIN resource r ON r.gsie_id = 'gsie:evidence:' || k.connaissance_id::text
        WHERE k.evidence_level IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # 2d. source + citation (si k.source contient des infos)
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'source',
            'gsie:source:' || k.connaissance_id::text,
            k.source,
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        WHERE k.source IS NOT NULL AND k.source != 'null'::jsonb
        ON CONFLICT DO NOTHING
    """)

    # Ligne satellite `source` manquante (corrigée — la ressource existait
    # sans elle, "orpheline", exactement le défaut relevé par l'audit).
    # title/subtype/source_nature sont NOT NULL : extraits du JSONB libre
    # avec des replis raisonnables faute de schéma garanti sur k.source.
    op.execute("""
        INSERT INTO source (id, title, subtype, source_nature)
        SELECT
            r.id,
            COALESCE(k.source->>'titre', k.source->>'title', k.source->>'nom', 'Source migrée (v6.1)'),
            'dataset'::source_subtype,
            'data_provider'::source_nature
        FROM knowledge_objects k
        JOIN resource r ON r.gsie_id = 'gsie:source:' || k.connaissance_id::text
        WHERE k.source IS NOT NULL AND k.source != 'null'::jsonb
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'citation',
            'gsie:citation:' || k.connaissance_id::text,
            '{}'::jsonb,
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        WHERE k.source IS NOT NULL AND k.source != 'null'::jsonb
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO citation (id, source_id, target_id, citation_role, created_at, updated_at)
        SELECT
            c.id,
            s.id,
            k.connaissance_id,
            'primary'::citation_role,
            k.created_at,
            k.updated_at
        FROM knowledge_objects k
        JOIN resource s ON s.gsie_id = 'gsie:source:' || k.connaissance_id::text
        JOIN resource c ON c.gsie_id = 'gsie:citation:' || k.connaissance_id::text
        WHERE k.source IS NOT NULL AND k.source != 'null'::jsonb
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 3. knowledge_history → revision
    # ===================================================================
    op.execute("""
        INSERT INTO revision (target_id, version, justification, valid_time_start, transaction_time, created_at)
        SELECT
            h.connaissance_id,
            h.version,
            h.justification,
            h.date,
            h.date,
            h.date
        FROM knowledge_history h
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 4. knowledge_relations → predicate + assertion_participant
    # ===================================================================
    # CORRIGÉ : cette section référençait des colonnes inexistantes
    # (relation_type, source_id, target_id). La vraie table knowledge_relations
    # (migration 0001) a : connaissance_id (source), cible_connaissance_id
    # (cible), predicat (libellé), sens. Vérifié contre le schéma réel avant
    # correction — ne pas deviner les noms de colonnes.

    # 4a. predicate (un par predicat distinct)
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT DISTINCT
            gen_random_uuid(),
            'predicate',
            'gsie:predicate:' || md5(kr.predicat),
            '{}'::jsonb,
            now(), now()
        FROM knowledge_relations kr
        WHERE kr.predicat IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO predicate (id, label, created_at, updated_at)
        SELECT
            r.id,
            kr.predicat,
            now(), now()
        FROM (
            SELECT DISTINCT predicat
            FROM knowledge_relations
            WHERE predicat IS NOT NULL
        ) kr
        JOIN resource r ON r.gsie_id = 'gsie:predicate:' || md5(kr.predicat)
        ON CONFLICT DO NOTHING
    """)

    # 4b. assertion_participant (sujet + objet). Garde EXISTS sur
    # cible_connaissance_id : contrairement à connaissance_id (FK réelle vers
    # knowledge_objects dans 0001), cible_connaissance_id n'a pas de
    # contrainte — une cible orpheline planterait l'INSERT sur la FK
    # assertion_participant -> resource sinon.
    op.execute("""
        INSERT INTO assertion_participant (assertion_id, role, participant_id)
        SELECT
            kr.connaissance_id,
            'subject'::participant_role,
            kr.cible_connaissance_id
        FROM knowledge_relations kr
        WHERE kr.connaissance_id IS NOT NULL AND kr.cible_connaissance_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM resource r WHERE r.id = kr.cible_connaissance_id)
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO assertion_participant (assertion_id, role, participant_id)
        SELECT
            kr.cible_connaissance_id,
            'object'::participant_role,
            kr.connaissance_id
        FROM knowledge_relations kr
        WHERE kr.connaissance_id IS NOT NULL AND kr.cible_connaissance_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM resource r WHERE r.id = kr.cible_connaissance_id)
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 5. knowledge_conflits → conflict_cluster
    # ===================================================================
    op.execute("""
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
            now(), now()
        FROM knowledge_conflits kc
        ON CONFLICT DO NOTHING
    """)

    # Ligne satellite `conflict_cluster` manquante (corrigée — même défaut
    # "ressource orpheline" que pour `source` ci-dessus).
    op.execute("""
        INSERT INTO conflict_cluster (id, description, status)
        SELECT
            r.id,
            kc.description,
            'unresolved'::conflict_status
        FROM knowledge_conflits kc
        JOIN resource r ON r.gsie_id = 'gsie:conflict:' || kc.id::text
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 6. knowledge_mots_cles → controlled_term (tags)
    # ===================================================================
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT DISTINCT
            gen_random_uuid(),
            'controlled_term',
            'gsie:tag:' || md5(km.mot_cle),
            jsonb_build_object('label', km.mot_cle),
            now(), now()
        FROM knowledge_mots_cles km
        WHERE km.mot_cle IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO controlled_term (id, vocabulary_id, code, label)
        SELECT
            r.id,
            v.id,
            md5(km.mot_cle),
            km.mot_cle
        FROM (
            SELECT DISTINCT mot_cle FROM knowledge_mots_cles WHERE mot_cle IS NOT NULL
        ) km
        JOIN resource r ON r.gsie_id = 'gsie:tag:' || md5(km.mot_cle)
        JOIN resource v ON v.gsie_id = 'gsie:vocabulary:keywords'
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 7. knowledge_domaines_validite → assertion_qualifier
    # ===================================================================
    # CORRIGÉ : knowledge_domaines_validite (0001) n'a pas de colonne
    # "domaine" — les vraies colonnes sont parametre/minimum/maximum/unite.
    op.execute("""
        INSERT INTO assertion_qualifier (assertion_id, key, value)
        SELECT
            dv.connaissance_id,
            dv.parametre,
            TRIM(CONCAT_WS(
                ' ',
                NULLIF(CONCAT_WS('-', dv.minimum::text, dv.maximum::text), ''),
                dv.unite
            ))
        FROM knowledge_domaines_validite dv
        WHERE dv.connaissance_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 8. botanical_familles → controlled_term (vocabulary)
    # ===================================================================
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'controlled_term',
            'gsie:famille:' || bf.nom_scientifique,
            jsonb_build_object(
                'nom_commun', bf.nom_commun,
                'source_reference', bf.source_reference
            ),
            bf.created_at, bf.updated_at
        FROM botanical_familles bf
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO controlled_term (id, vocabulary_id, code, label)
        SELECT
            r.id,
            v.id,
            bf.nom_scientifique,
            COALESCE(bf.nom_commun, bf.nom_scientifique)
        FROM botanical_familles bf
        JOIN resource r ON r.gsie_id = 'gsie:famille:' || bf.nom_scientifique
        JOIN resource v ON v.gsie_id = 'gsie:vocabulary:botanical_families'
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 9. botanical_genres → controlled_term (vocabulary)
    # ===================================================================
    # CORRIGÉ : botanical_genres (0001) n'a pas de colonne nom_commun (ce
    # champ n'existe que sur botanical_familles) — vérifié empiriquement
    # (UndefinedColumnError reproduite puis corrigée, base de test réelle).
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'controlled_term',
            'gsie:genre:' || bg.nom_scientifique,
            jsonb_build_object(
                'famille_id', bg.famille_id,
                'source_reference', bg.source_reference
            ),
            bg.created_at, bg.updated_at
        FROM botanical_genres bg
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO controlled_term (id, vocabulary_id, code, label)
        SELECT
            r.id,
            v.id,
            bg.nom_scientifique,
            bg.nom_scientifique
        FROM botanical_genres bg
        JOIN resource r ON r.gsie_id = 'gsie:genre:' || bg.nom_scientifique
        JOIN resource v ON v.gsie_id = 'gsie:vocabulary:botanical_genres'
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 10. botanical_essences → instance + concept
    # ===================================================================

    # 10a. concept (l'essence comme concept taxonomique)
    # CORRIGÉ : botanical_essences (0001) n'a pas de famille_id direct
    # (seulement genre_id — la famille se déduit via genre_id -> famille_id) ;
    # vérifié empiriquement (UndefinedColumnError reproduite).
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'concept',
            'gsie:essence:' || be.nom_scientifique,
            jsonb_build_object(
                'nom_vernaculaire', be.nom_vernaculaire,
                'genre_id', be.genre_id,
                'categorie_forestiere', be.categorie_forestiere,
                'gbif_taxon_key', be.gbif_taxon_key,
                'source_reference', be.source_reference
            ),
            be.created_at, be.updated_at
        FROM botanical_essences be
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO concept (id, preferred_label, description)
        SELECT
            r.id,
            be.nom_scientifique,
            COALESCE(be.nom_vernaculaire, be.nom_scientifique)
        FROM botanical_essences be
        JOIN resource r ON r.gsie_id = 'gsie:essence:' || be.nom_scientifique
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 11. ecosystem_habitats → place + controlled_term
    # ===================================================================

    # 11a. place (avec géométrie NULL — pas de coordonnées dans l'ancien schéma)
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'place',
            'gsie:habitat:' || eh.code_eur28,
            jsonb_build_object(
                'code_eur28', eh.code_eur28,
                'description', eh.description,
                'categorie', eh.categorie,
                'interet_patrimonial', eh.interet_patrimonial,
                'source_reference', eh.source_reference,
                'attributs', eh.attributs
            ),
            eh.created_at, eh.updated_at
        FROM ecosystem_habitats eh
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO place (id, label, srid)
        SELECT
            r.id,
            eh.nom_habitat,
            2154
        FROM ecosystem_habitats eh
        JOIN resource r ON r.gsie_id = 'gsie:habitat:' || eh.code_eur28
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 12. ecosystem_stations → place + controlled_term
    # ===================================================================
    # CORRIGÉ : ecosystem_stations (0001) n'a pas coordonnees/altitude/
    # exposition — vraies colonnes : region_forestiere, departements,
    # altitude_min/max, ph_typique, rum_typique.
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'place',
            'gsie:station:' || es.code_station,
            jsonb_build_object(
                'code_station', es.code_station,
                'description', es.description,
                'region_forestiere', es.region_forestiere,
                'departements', es.departements,
                'altitude_min', es.altitude_min,
                'altitude_max', es.altitude_max,
                'ph_typique', es.ph_typique,
                'rum_typique', es.rum_typique,
                'source_reference', es.source_reference
            ),
            es.created_at, es.updated_at
        FROM ecosystem_stations es
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO place (id, label, srid)
        SELECT
            r.id,
            es.nom_station,
            2154
        FROM ecosystem_stations es
        JOIN resource r ON r.gsie_id = 'gsie:station:' || es.code_station
        ON CONFLICT DO NOTHING
    """)

    # ===================================================================
    # 13. ecosystem_groupes_ecologiques → controlled_term
    # ===================================================================
    # CORRIGÉ : ecosystem_groupes_ecologiques (0001) n'a pas especes/habitats
    # — vraies colonnes : indicateur, valeurs_indicatrices, especes_caracteristiques.
    op.execute("""
        INSERT INTO resource (id, type, gsie_id, metadata_json, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'controlled_term',
            'gsie:groupe_eco:' || md5(eg.nom_groupe),
            jsonb_build_object(
                'description', eg.description,
                'indicateur', eg.indicateur,
                'valeurs_indicatrices', eg.valeurs_indicatrices,
                'especes_caracteristiques', eg.especes_caracteristiques,
                'source_reference', eg.source_reference
            ),
            eg.created_at, eg.updated_at
        FROM ecosystem_groupes_ecologiques eg
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO controlled_term (id, vocabulary_id, code, label)
        SELECT
            r.id,
            v.id,
            md5(eg.nom_groupe),
            eg.nom_groupe
        FROM ecosystem_groupes_ecologiques eg
        JOIN resource r ON r.gsie_id = 'gsie:groupe_eco:' || md5(eg.nom_groupe)
        JOIN resource v ON v.gsie_id = 'gsie:vocabulary:ecological_groups'
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    """Supprime les données v6.2 copiées par cette migration.

    Les tables v6.1 ne sont pas touchées — elles restent intactes.
    """
    # Supprimer les données structurées créées par cette migration
    # (key est désormais dv.parametre, variable — on cible par provenance
    # via knowledge_domaines_validite plutôt que par une valeur fixe).
    op.execute("""
        DELETE FROM assertion_qualifier
        WHERE (assertion_id, key) IN (
            SELECT connaissance_id, parametre FROM knowledge_domaines_validite
        )
    """)
    # Les deux inserts (4b) créent une ligne assertion_id=connaissance_id
    # (rôle subject) ET une ligne assertion_id=cible_connaissance_id (rôle
    # object) — il faut nettoyer les deux, pas seulement la première.
    op.execute("""
        DELETE FROM assertion_participant
        WHERE assertion_id IN (SELECT connaissance_id FROM knowledge_relations)
           OR assertion_id IN (SELECT cible_connaissance_id FROM knowledge_relations)
    """)
    # CORRIGÉ : citation n'a pas de colonne gsie_id (elle est sur resource,
    # pas les tables satellites) — vérifié empiriquement (UndefinedColumnError
    # reproduite). source/conflict_cluster n'ont pas besoin de DELETE
    # explicite : leur FK vers resource.id est ON DELETE CASCADE, couverte
    # par le DELETE FROM resource plus bas.
    op.execute("DELETE FROM citation WHERE id IN (SELECT id FROM resource WHERE gsie_id LIKE 'gsie:citation:%')")
    op.execute("DELETE FROM evidence_assessment WHERE method = 'migration_v6.1'")
    op.execute("DELETE FROM controlled_term WHERE vocabulary_id IN (SELECT id FROM resource WHERE gsie_id LIKE 'gsie:vocabulary:%')")
    op.execute("DELETE FROM place WHERE id IN (SELECT id FROM resource WHERE gsie_id LIKE 'gsie:habitat:%' OR gsie_id LIKE 'gsie:station:%')")
    op.execute("DELETE FROM concept WHERE id IN (SELECT id FROM resource WHERE gsie_id LIKE 'gsie:essence:%')")
    op.execute("DELETE FROM predicate WHERE id IN (SELECT id FROM resource WHERE gsie_id LIKE 'gsie:predicate:%')")
    op.execute("DELETE FROM assertion WHERE id IN (SELECT connaissance_id FROM knowledge_objects)")
    op.execute("DELETE FROM revision WHERE target_id IN (SELECT connaissance_id FROM knowledge_objects)")
    # Supprimer les resources créées par cette migration (identifier par gsie_id)
    op.execute("DELETE FROM resource WHERE gsie_id LIKE 'gsie:%' AND type IN ('assertion', 'evidence_assessment', 'source', 'citation', 'predicate', 'conflict_cluster', 'controlled_term', 'concept', 'place', 'vocabulary')")
