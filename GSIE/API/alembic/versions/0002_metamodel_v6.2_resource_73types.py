"""Migration 0002 — Métamodèle v6.2 : création du schéma (tables vides)

Étape 1/4 du plan de migration progressive (ADR-004 Validated).

Cette migration crée UNIQUEMENT le schéma v6.2 (tables + enums + index),
SANS toucher aux données existantes. Les tables anciennes (knowledge_objects,
botanical_*, ecosystem_*) restent intactes. La migration des données se fait
dans la migration 0003.

Plan ADR-004 :
- 0002 (cette migration) : créer resource + 73 tables v6.2 (vides) + enums + index
- 0003 : copier les données des tables v6.1 vers les tables v6.2
- 0004 : bascule des moteurs (repository PG sur schéma v6.2)
- 0005 : supprimer les anciennes tables v6.1 après validation

Rollback : DROP des tables v6.2 + DROP des enums. Les tables v6.1 ne sont
pas touchées — elles restent disponibles en cas de repli.

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

# Tous les enums du métamodèle v6.2 (54 enums)
_ENUMS: list[tuple[str, list[str]]] = [
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
    ("ecosystem_service_category", ["regulation", "support", "provisioning", "cultural"]),
    ("goal_priority", ["primary", "secondary", "tertiary"]),
    ("constraint_severity", ["blocking", "limiting", "conditional"]),
    ("propagation_method", ["bayesian", "weighted_average", "dempster_shafer", "fuzzy"]),
    ("production_method", ["inference", "correlation", "synthesis", "expert_judgment", "model_output", "extraction", "validation"]),
    ("terrain_session_type", ["inventory", "martelage", "monitoring", "diagnosis", "research", "calibration"]),
    ("sync_status", ["synced", "partial", "pending", "failed"]),
    ("permission", ["read", "write", "delete", "admin", "rgpd_manager"]),
    # Enums métier (types 74-80 — audit ONF/CNPF)
    ("management_plan_type", ["psg", "amf", "rtg", "custom"]),
    ("plan_status", ["draft", "submitted", "approved", "active", "revision", "expired", "cancelled"]),
    ("intervention_type", ["planting", "thinning", "clear_cut", "selective_cut", "shelterwood", "coppicing", "pruning", "clearing", "fertilization", "drainage", "road_work", "protection", "inventory", "other"]),
    ("intervention_status", ["planned", "scheduled", "in_progress", "completed", "cancelled", "delayed"]),
    ("economic_category", ["cost", "revenue", "subsidy", "investment", "market_price"]),
    ("regulation_domain", ["forest_code", "psg_obligations", "natura_2000", "water_protection", "biodiversity_protection", "urban_planning", "environmental_impact", "other"]),
    ("compliance_status", ["compliant", "non_compliant", "pending_check", "waiver", "not_applicable"]),
    ("outcome_status", ["pending", "in_progress", "achieved", "partially_achieved", "not_achieved", "abandoned"]),
    ("administrative_level", ["national", "regional", "departmental", "forest_domain", "triage", "canton", "parcel", "series"]),
]


def upgrade() -> None:
    # --- 1. Enums PostgreSQL ---
    for enum_name, values in _ENUMS:
        op.execute(
            f"CREATE TYPE {enum_name} AS ENUM ({', '.join(f"'{v}'" for v in values)})"
        )

    # --- 2. Table racine resource (ADR-001) ---
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
    # Index composite pour listings par type avec pagination temporelle
    op.create_index("ix_resource_type_created", "resource", ["type", sa.text("created_at DESC")])

    # --- 3. Auto-création des 73 tables depuis les modèles SQLAlchemy ---
    # Import des modèles pour peupler Base.metadata
    from gsie_api.infrastructure.models import Base  # noqa: F401
    from gsie_api.infrastructure.models import (  # noqa: F401
        assertion, dynamics, ecology, fair_rgpd, governance,
        models_ai, observation, prov, provenance, reasoning,
        spatial_temporal, temporal_engine,
    )
    from gsie_api.infrastructure.models import junctions  # noqa: F401
    from gsie_api.infrastructure.models import outbox  # noqa: F401

    # Créer toutes les tables sauf resource (déjà créée ci-dessus)
    tables_to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name != "resource"
    ]
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=tables_to_create,
    )

    # --- 4. Index de performance (audit H4) ---
    # Index sur FK fréquemment jointes
    op.create_index("ix_assertion_predicate", "assertion", ["predicate_id"])
    op.create_index("ix_assertion_spatial", "assertion", ["spatial_scope_id"])
    op.create_index("ix_assertion_temporal", "assertion", ["temporal_context_id"])
    op.create_index("ix_observation_subject", "observation", ["subject_id"])
    op.create_index("ix_revision_target", "revision", ["target_id"])
    op.create_index("ix_revision_author", "revision", ["author_id"])
    op.create_index("ix_citation_target", "citation", ["target_id"])

    # ⚠️ NE PAS migrer les données ici — c'est le rôle de la migration 0003.
    # Les tables anciennes (knowledge_objects, botanical_*, ecosystem_*)
    # restent intactes et disponibles.


def downgrade() -> None:
    # --- 1. Supprimer les tables v6.2 (uniquement) ---
    from gsie_api.infrastructure.models import Base  # noqa: F401
    from gsie_api.infrastructure.models import (  # noqa: F401
        assertion, dynamics, ecology, fair_rgpd, governance,
        models_ai, observation, prov, provenance, reasoning,
        spatial_temporal, temporal_engine,
    )
    from gsie_api.infrastructure.models import junctions  # noqa: F401
    from gsie_api.infrastructure.models import outbox  # noqa: F401

    # Drop uniquement les tables v6.2 (celles dans Base.metadata)
    # Les tables v6.1 (knowledge_objects, botanical_*, ecosystem_*) ne sont
    # PAS dans Base.metadata — elles ne seront pas touchées.
    tables_to_drop = [
        t for t in reversed(Base.metadata.sorted_tables)
        if t.name != "resource"
    ]
    Base.metadata.drop_all(
        bind=op.get_bind(),
        tables=tables_to_drop,
    )

    op.drop_table("resource")

    # --- 2. Supprimer les enums ---
    for enum_name, _ in _ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    # Les tables v6.1 sont préservées — rollback sûr.
