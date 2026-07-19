"""Validation dynamique des données par type de resource.

Valide les champs obligatoires et les enums pour chaque type avant
l'insertion en DB. Évite d'envoyer n'importe quoi dans `data`.
"""

from enum import Enum
from typing import Any

from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    ActivityType,
    AgentType,
    CapabilityType,
    ClaimKind,
    ConsentScope,
    ConstraintType,
    CorrelationMethod,
    CorrelationStrength,
    DatasetPurpose,
    EcologicalProcessType,
    EvidenceLevel,
    FeatureSourceType,
    FlowDirection,
    FlowType,
    GoalType,
    HealthRiskSeverity,
    HypothesisStatus,
    LegalBasis,
    LifecycleStatus,
    MaterielBaseCategory,
    MediaType,
    ModelType,
    PhenomenonType,
    PIDType,
    ProviderType,
    QualityDimension,
    QuestionType,
    RelationCategory,
    RuleSubtype,
    SampleType,
    ScaleLevel,
    ScenarioSubtype,
    ScenarioType,
    SilviculturalSystemCategory,
    SourceNature,
    SourceSubtype,
    StateType,
    TemporalGranularity,
    UncertaintyType,
    UsageRights,
    ValueType,
)

# Mappe type_name → {champ: enum_class}
# Seuls les champs enum sont validés ici. Les champs obligatoires (non-None) sont listés séparément.
_ENUM_FIELDS: dict[str, dict[str, type[Enum]]] = {
    "assertion": {
        "claim_kind": ClaimKind,
        "lifecycle_status": LifecycleStatus,
        "rule_subtype": RuleSubtype,
    },
    "observation": {},
    "result": {"value_type": ValueType},
    "uncertainty": {"type": UncertaintyType},
    "quality_assessment": {"dimension": QualityDimension},
    "activity": {"type": ActivityType},
    "agent": {"type": AgentType},
    "source": {"subtype": SourceSubtype, "source_nature": SourceNature},
    "media": {"type": MediaType},
    "temporal_context": {"granularity": TemporalGranularity},
    "model": {"type": ModelType},
    "dataset": {"purpose": DatasetPurpose},
    "distribution": {"access_method": AccessMethod},
    "feature": {"source_type": FeatureSourceType},
    "scale_context": {"level": ScaleLevel},
    "phenomenon": {"phenomenon_type": PhenomenonType},
    "ecological_process": {"process_type": EcologicalProcessType},
    "relation_type": {"category": RelationCategory},
    "correlation": {
        "method": CorrelationMethod,
        "strength": CorrelationStrength,
        "lifecycle_status": LifecycleStatus,
    },
    "capability": {
        "capability_type": CapabilityType,
        "provider_type": ProviderType,
    },
    "scenario": {
        "scenario_type": ScenarioType,
        "scenario_subtype": ScenarioSubtype,
    },
    "question": {"question_type": QuestionType},
    "hypothesis": {"status": HypothesisStatus},
    "rights_statement": {"usage_rights": UsageRights},
    "conflict_cluster": {},  # status est un enum ConflictStatus mais pas dans la mappe encore
    "flow": {"flow_type": FlowType, "direction": FlowDirection},
    "goal": {"goal_type": GoalType},
    "constraint": {"constraint_type": ConstraintType},
    "sample": {"sample_type": SampleType},
    "consent": {"scope": ConsentScope, "legal_basis": LegalBasis},
    "persistent_identifier": {"pid_type": PIDType},
    "evidence_assessment": {"level": EvidenceLevel},
    "ecological_state": {
        "state_type": StateType,
    },
    # RFC-0016 — schéma forestier spécialisé (types 81-90, tranches 1-5/10)
    "autecology_profile": {"evidence_level": EvidenceLevel},
    "site_index_model": {},
    "fertility_class": {},
    "station_type": {},
    "station_observation": {},
    "silvicultural_system": {"category": SilviculturalSystemCategory},
    "silvicultural_rule": {"evidence_level": EvidenceLevel},
    "provenance_material": {"base_material_category": MaterielBaseCategory},
    "diagnostic_protocol": {},
    "health_risk": {"severity": HealthRiskSeverity},
}

# Champs obligatoires (non-None) par type
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "assertion": ["claim_kind", "lifecycle_status"],
    "observation": ["subject_id"],
    "result": ["observation_id", "value_type"],
    "method": ["name", "description"],
    "instrument": ["name", "type"],
    "uncertainty": ["type"],
    "quality_assessment": ["target_id", "dimension", "score", "method", "assessed_at"],
    "activity": ["type", "started_at"],
    "agent": ["name", "type"],
    "source": ["title", "subtype", "source_nature"],
    "citation": ["source_id", "target_id", "citation_role"],
    "unit": ["symbol", "name"],
    "temporal_context": [
        "valid_time_start",
        "transaction_time_start",
        "granularity",
    ],
    "media": ["type", "url", "mime_type"],
    "model": ["name", "type", "description"],
    "model_run": ["model_version_id", "started_at"],
    "dataset": ["title", "description"],
    "model_version": ["model_id", "version"],
    "dataset_version": ["dataset_id", "version"],
    "data_asset": [
        "dataset_version_id",
        "format",
        "size_bytes",
        "checksum",
        "archived_at",
    ],
    "distribution": ["dataset_version_id", "access_method", "licence"],
    "feature": ["name", "description", "source_type"],
    "feature_set": ["name", "description"],
    "inference": [
        "model_version_id",
        "feature_set_id",
        "confidence",
        "inferred_at",
    ],
    "scale_context": ["level"],
    "phenomenon": ["phenomenon_type", "name"],
    "ecological_process": ["process_type", "name"],
    "relation_type": ["category", "label", "description"],
    "sampling_event": ["name", "spatial_design"],
    "trait_definition": ["name", "description"],
    "trait_value": ["trait_definition_id", "entity_id"],
    "question": ["text", "question_type", "asked_at"],
    "hypothesis": ["question_id", "text", "status"],
    "decision": ["decided_by", "decision_text", "rationale", "decided_at"],
    "recommendation": [
        "recommended_by",
        "recommendation_text",
        "confidence",
    ],
    "scenario": ["name", "scenario_type", "description"],
    "correlation": ["method", "strength", "confidence"],
    "ecosystem_service": ["name", "description"],
    "capability": [
        "name",
        "capability_type",
        "provider_type",
        "provider_id",
    ],
    "rights_statement": ["licence", "usage_rights"],
    "access_policy": ["target_id", "principal", "permission"],
    "sensitivity_classification": ["target_id", "level", "reason"],
    "conflict_cluster": ["description"],
    "flow": [
        "flow_type",
        "source_id",
        "sink_id",
        "magnitude",
        "magnitude_unit_id",
    ],
    "confidence_graph": ["root_resource_id", "computed_at"],
    "goal": ["goal_type", "name", "description"],
    "constraint": ["constraint_type", "name", "description"],
    "knowledge_lineage": ["root_id", "computed_at"],
    "experiment": ["name", "conducted_by"],
    "terrain_session": ["name", "session_type", "started_at"],
    "ecological_state": ["spatial_scope_id", "state_type"],
    "sample": ["sample_type", "subject_id", "material"],
    "consent": [
        "data_subject_id",
        "purpose",
        "granted_at",
        "legal_basis",
    ],
    "data_subject": ["agent_id", "pseudonymized_id"],
    "persistent_identifier": [
        "target_id",
        "pid_type",
        "value",
        "authority",
        "registered_at",
    ],
    "concept": ["preferred_label", "description"],
    "vocabulary": ["name", "namespace", "description"],
    "controlled_term": ["vocabulary_id", "code", "label"],
    "instance": ["concept_id"],
    "predicate": ["label"],
    "evidence_assessment": ["assertion_id", "level", "method", "evaluated_at"],
    # RFC-0016 — schéma forestier spécialisé (§3.1, §5 Phase A point 3 : porte
    # de validation, aucune de ces entités sans ses champs non négociables,
    # même à travers l'API générique de resources, pas seulement via les
    # schémas Pydantic des engines).
    "autecology_profile": [
        "species_entity_id",
        "variable",
        "evidence_level",
        "source_id",
    ],
    "site_index_model": [
        "species_entity_id",
        "name",
        "method",
        "reference_age_years",
        "age_convention",
        "calibration_region",
        "source_id",
    ],
    "fertility_class": [
        "species_entity_id",
        "site_index_model_id",
        "class_label",
        "reference_age_years",
        "calibration_region",
        "source_id",
    ],
    "station_type": ["guide", "guide_version", "validity_zone_description", "source_id"],
    "station_observation": ["plot_reference", "observed_at", "source_id"],
    "silvicultural_system": ["name", "category", "source_id"],
    "silvicultural_rule": [
        "required_context",
        "trigger",
        "action",
        "intensity",
        "evidence_level",
        "source_id",
    ],
    "provenance_material": [
        "species_entity_id",
        "provenance_region",
        "base_material",
        "base_material_category",
        "aid_eligible",
        "decree_version",
        "source_id",
    ],
    "diagnostic_protocol": [
        "name",
        "version",
        "criteria_description",
        "thresholds_description",
        "source_id",
    ],
    "health_risk": ["subject_id", "symptom_observed", "observed_at", "source_id"],
}


def validate_resource_data(type_name: str, data: dict[str, Any]) -> list[str]:
    """Valide les données d'une resource selon son type.

    Args:
        type_name: Type de resource (ex. "assertion", "observation").
        data: Champs spécifiques au type.

    Returns:
        Liste des erreurs de validation (vide si OK).
    """
    errors: list[str] = []

    # 1. Champs obligatoires
    required = _REQUIRED_FIELDS.get(type_name, [])
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Champ obligatoire manquant : {field}")

    # 2. Validation des enums
    enum_fields = _ENUM_FIELDS.get(type_name, {})
    for field, enum_cls in enum_fields.items():
        if field in data and data[field] is not None:
            value = data[field]
            valid_values = {e.value for e in enum_cls}
            if value not in valid_values:
                errors.append(
                    f"Valeur invalide pour {field} : '{value}'. "
                    f"Valeurs acceptées : {sorted(valid_values)}"
                )

    # 3. Validation de longueur des chaînes (protection DoS, OWASP A04)
    max_string_length = 10000
    for field, value in data.items():
        if isinstance(value, str) and len(value) > max_string_length:
            errors.append(f"Champ {field} trop long : {len(value)} chars (max {max_string_length})")

    # 4. Validation du nombre de champs (payload limit)
    max_fields = 50
    if len(data) > max_fields:
        errors.append(f"Trop de champs : {len(data)} (max {max_fields})")

    return errors
