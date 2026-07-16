"""Migration 0002 — Métamodèle v6.2 : table racine resource + 73 types

⚠️ AVERTISSEMENT CRITIQUE — NE PAS EXÉCUTER CONTRE UNE BASE AVEC DONNÉES RÉELLES ⚠️

Cette migration a 3 problèmes identifiés par audit (2026-07-16) :
1. DOWNGRADE DESTRUCTIF : downgrade() drop toutes les tables (nouvelles ET
   anciennes) sans recréer les tables v6.1. Un `alembic downgrade -1` efface
   plus de données que l'upgrade n'en a créé.
2. DONNÉES FANTÔMES : pour botanical_familles, ecosystem_habitats,
   knowledge_conflits — seule une ligne vide est créée dans `resource` sans
   la ligne fille correspondante. Les données métier (nom_scientifique,
   code_eur28, description, source) sont perdues.
3. TABLES NON MIGRÉES : 7 tables sur 12 de l'ancien schéma ne sont migrées
   nulle part (knowledge_relations, knowledge_mots_cles,
   knowledge_domaines_validite, botanical_genres, botanical_essences,
   ecosystem_stations, ecosystem_groupes_ecologiques). Le docstring
   prétendait traiter knowledge_relations — c'était faux.

Cette migration reste utilisable sur une base VIDE (création de schéma pur)
mais ne doit JAMAIS être appliquée sur une base contenant des données
v6.1 tant que les 3 problèmes ne sont pas corrigés.

Décision en attente : ADR-004 (migration progressive en 4 étapes) vs
RFC-0012 (big bang) — contradiction non réconciliée à ce jour.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-16
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Enums PostgreSQL ---
    enums = [
        ("claim_kind", ["observation", "relation", "rule", "threshold", "model", "classification", "absence"]),
        ("lifecycle_status", ["draft", "proposed", "accepted", "superseded", "rejected", "deprecated"]),
        ("value_type", ["numeric", "term", "media_ref", "entity_ref", "computed", "absence"]),
        ("source_nature", ["data_provider", "knowledge_provider", "reference", "expert_statement", "regulatory", "model_output"]),
        ("source_subtype", ["publication", "dataset", "api", "person", "organisation", "regulatory_text", "expert_statement"]),
        ("access_method", ["api_rest", "api_graphql", "ogc_wms", "ogc_wfs", "ogc_wmts", "ogc_wcs", "stac_api", "file_download", "file_import", "publication_text", "knowledge_extraction"]),
        ("scale_level", ["leaf", "tree", "plot", "stand", "forest", "massif", "landscape", "region", "country", "biome", "earth"]),
        ("phenomenon_type", ["drought", "storm", "pest_outbreak", "pathogen_outbreak", "wildfire", "flood", "succession", "migration", "competition", "invasion", "decline", "regeneration", "phenology_shift", "other"]),
        ("ecological_process_type", ["photosynthesis", "transpiration", "respiration", "growth", "decomposition", "nutrient_cycling", "mycorrhization", "nitrogen_fixation", "pollination", "seed_dispersal", "herbivory", "predation", "competition", "facilitation", "succession", "carbon_sequestration", "water_cycling", "other"]),
        ("relation_category", ["causal", "spatial", "temporal", "ecological", "taxonomic", "hydrological", "genetic", "trophic", "competition", "facilitation", "host_pathogen", "predator_prey", "other"]),
        ("correlation_method", ["pearson", "spearman", "kendall", "bayesian", "mutual_information", "ai", "expert", "literature", "meta_analysis"]),
        ("capability_type", ["observe", "predict", "inventory", "diagnose", "simulate", "recommend", "correlate", "reason", "validate", "learn", "extract", "assess_evidence"]),
        ("rule_subtype", ["inference", "scientific", "business", "regulatory"]),
        ("dataset_purpose", ["production", "training", "evaluation", "reference"]),
        ("sample_type", ["soil", "leaf", "bark", "wood_core", "water", "root", "seed", "tissue", "soil_water", "litter", "other"]),
        ("legal_basis", ["consent", "contract", "legal_obligation", "vital_interest", "public_interest", "legitimate_interest", "research"]),
        ("pid_type", ["doi", "purl", "orcid", "ror", "gbif_taxonkey", "wikidata_qid", "inpn_taxref", "issn", "handle", "ark", "urn", "gsie_uri"]),
        ("flow_type", ["carbon", "water", "nitrogen", "phosphorus", "nutrient", "energy", "seed", "pollen", "gene", "pathogen", "spore", "biomass", "sediment", "other"]),
        ("goal_type", ["biodiversity", "production", "risk_reduction", "conservation", "restoration", "carbon_sequestration", "water_protection", "soil_protection", "recreation", "research", "regulatory", "other"]),
        ("constraint_type", ["regulatory", "budget", "accessibility", "weather", "equipment", "ecological", "temporal", "social", "technical", "other"]),
        ("scenario_subtype", ["rcp_2.6", "rcp_4.5", "rcp_8.5", "ssp1_2.6", "ssp3_7.0", "ssp5_8.5", "drias_2020", "clear_cut", "selective_thinning", "shelterwood", "coppice", "no_intervention", "adaptive", "wildfire", "storm", "pest_outbreak", "baseline"]),
        ("scenario_type", ["sylvicultural", "climatic", "management", "disturbance", "baseline"]),
        ("agent_type", ["person", "organisation", "software"]),
        ("activity_type", ["extraction", "transformation", "ingestion", "validation", "revision", "simulation"]),
        ("media_type", ["image", "audio", "video", "document"]),
        ("model_type", ["growth", "dynamics", "propagation", "climate", "ml"]),
        ("evidence_level", ["A", "B", "C", "D", "E", "F"]),
        ("temporal_granularity", ["instant", "day", "month", "year", "period", "range"]),
        ("participant_role", ["subject", "object", "context"]),
        ("citation_role", ["primary", "supporting", "contradicting", "cited"]),
        ("quality_dimension", ["completeness", "positional_accuracy", "temporal_accuracy", "thematic_accuracy", "logical_consistency"]),
        ("uncertainty_type", ["confidence_interval", "standard_error", "range", "qualitative"]),
        ("usage_rights", ["open", "restricted", "private"]),
        ("sensitivity_level", ["public", "restricted", "sensitive", "critical"]),
        ("conflict_status", ["open", "resolved_by_consensus", "resolved_by_arbitrage", "unresolved"]),
        ("correlation_strength", ["negligible", "weak", "moderate", "strong", "very_strong"]),
        ("question_type", ["scientific", "operational", "diagnostic", "predictive"]),
        ("hypothesis_status", ["proposed", "testing", "supported", "refuted", "inconclusive"]),
        ("provider_type", ["engine", "application"]),
        ("consent_scope", ["full", "anonymized_only", "aggregated_only"]),
        ("flow_direction", ["source_to_sink", "bidirectional"]),
        ("state_type", ["health", "vitality", "risk", "resilience", "biodiversity", "productivity", "integrity"]),
        ("ecological_grade", ["excellent", "good", "moderate", "poor", "critical"]),
        ("trend", ["improving", "stable", "declining", "unknown"]),
        ("feature_source_type", ["observation", "trait", "computed", "external"]),
        # Enums supplémentaires (audit)
        ("ecosystem_service_category", ["regulation", "support", "provisioning", "cultural"]),
        ("goal_priority", ["primary", "secondary", "tertiary"]),
        ("constraint_severity", ["blocking", "limiting", "conditional"]),
        ("propagation_method", ["bayesian", "weighted_average", "dempster_shafer", "fuzzy"]),
        ("production_method", ["inference", "correlation", "synthesis", "expert_judgment", "model_output", "extraction", "validation"]),
        ("terrain_session_type", ["inventory", "martelage", "monitoring", "diagnosis", "research", "calibration"]),
        ("sync_status", ["synced", "partial", "pending", "failed"]),
    ]

    for enum_name, values in enums:
        op.execute(
            f"CREATE TYPE {enum_name} AS ENUM ({', '.join(f"'{v}'" for v in values)})"
        )

    # --- Table racine resource (ADR-001) ---
    op.create_table(
        "resource",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("gsie_id", sa.String(100), unique=True, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_resource_type", "resource", ["type"])
    op.create_index("ix_resource_gsie_id", "resource", ["gsie_id"])
    op.create_index("ix_resource_deleted_at", "resource", ["deleted_at"])

    # --- Auto-création des 73 tables depuis les modèles SQLAlchemy ---
    # Import des modèles pour peupler Base.metadata
    from gsie_api.infrastructure.models import Base  # noqa: F401
    from gsie_api.infrastructure.models import (  # noqa: F401
        assertion, dynamics, ecology, fair_rgpd, governance,
        models_ai, observation, prov, provenance, reasoning,
        spatial_temporal, temporal_engine,
    )
    from gsie_api.infrastructure.models import junctions  # noqa: F401 — 17 tables n:m
    from gsie_api.infrastructure.models import outbox  # noqa: F401 — Outbox/Inbox (ADR-005)

    # Créer toutes les tables sauf resource (déjà créée ci-dessus)
    tables_to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name != "resource"
    ]
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=tables_to_create,
    )

    # --- Migration des données existantes ---

    # knowledge_objects → resource + assertion
    op.execute("""
        INSERT INTO resource (id, type, created_at, updated_at)
        SELECT connaissance_id, 'assertion', created_at, updated_at
        FROM knowledge_objects
        ON CONFLICT DO NOTHING
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
        ON CONFLICT DO NOTHING
    """)

    # knowledge_history → revision
    op.execute("""
        INSERT INTO revision (target_id, version, justification, valid_time_start, transaction_time, created_at)
        SELECT connaissance_id, version, justification, date, date, date
        FROM knowledge_history
    """)

    # knowledge_conflits → conflict_cluster
    op.execute("""
        INSERT INTO resource (id, type, created_at, updated_at)
        SELECT gen_random_uuid(), 'conflict_cluster', now(), now()
        FROM knowledge_conflits
    """)

    # botanical_familles → vocabulary + controlled_term
    op.execute("""
        INSERT INTO resource (id, type, created_at, updated_at)
        SELECT gen_random_uuid(), 'vocabulary', created_at, updated_at
        FROM botanical_familles
    """)

    # ecosystem_habitats → place
    op.execute("""
        INSERT INTO resource (id, type, created_at, updated_at)
        SELECT gen_random_uuid(), 'place', created_at, updated_at
        FROM ecosystem_habitats
    """)


def downgrade() -> None:
    # Supprimer les tables du métamodèle v6.2 (sauf resource en dernier)
    from gsie_api.infrastructure.models import Base  # noqa: F401
    from gsie_api.infrastructure.models import (  # noqa: F401
        assertion, dynamics, ecology, fair_rgpd, governance,
        models_ai, observation, prov, provenance, reasoning,
        spatial_temporal, temporal_engine,
    )
    from gsie_api.infrastructure.models import junctions  # noqa: F401
    from gsie_api.infrastructure.models import outbox  # noqa: F401

    tables_to_drop = [
        t for t in reversed(Base.metadata.sorted_tables)
        if t.name != "resource"
    ]
    Base.metadata.drop_all(
        bind=op.get_bind(),
        tables=tables_to_drop,
    )

    op.drop_table("resource")

    # Supprimer les enums
    enum_names = [
        "claim_kind", "lifecycle_status", "value_type", "source_nature",
        "source_subtype", "access_method", "scale_level", "phenomenon_type",
        "ecological_process_type", "relation_category", "correlation_method",
        "capability_type", "rule_subtype", "dataset_purpose", "sample_type",
        "legal_basis", "pid_type", "flow_type", "goal_type", "constraint_type",
        "scenario_subtype", "scenario_type", "agent_type", "activity_type",
        "media_type", "model_type", "evidence_level", "temporal_granularity",
        "participant_role", "citation_role", "quality_dimension", "uncertainty_type",
        "usage_rights", "sensitivity_level", "conflict_status", "correlation_strength",
        "question_type", "hypothesis_status", "provider_type", "consent_scope",
        "flow_direction", "state_type", "ecological_grade", "trend", "feature_source_type",
        "ecosystem_service_category", "goal_priority", "constraint_severity",
        "propagation_method", "production_method", "terrain_session_type", "sync_status",
    ]
    for enum_name in enum_names:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
