"""Index sur FK non indexees + CHECK constraints metier.

Audit DB 2026-07-27 (P0-3, P1-6) :
- 110 FK sur 323 n'avaient pas d'index -> seq scans sur tables coeur
  (recommendation, correlation, assertion, flow)
- 8 CHECK seulement sur 116 tables -> integrite metier reposant
  uniquement sur Pydantic

Index : CREATE INDEX CONCURRENTLY non supporte en migration Alembic
(transaction DDL). On utilise CREATE INDEX IF NOT EXISTS standard.

Revision ID: 20260727_0003
Revises: 20260726_0002
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0003"
down_revision: str | None = "20260726_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 110 index sur FK non indexees (audit programmatique de Base.metadata,
# voir GSIE-PROMPT correspondant — liste exhaustive dans le rapport d'audit)
_INDEXES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    # (index_name, table_name, (column,))
    ("idx_activity_method_id", "activity", ("method_id",)),
    ("idx_assertion_temporal_context_id", "assertion", ("temporal_context_id",)),
    ("idx_assertion_scale_context_id", "assertion", ("scale_context_id",)),
    ("idx_assertion_spatial_scope_id", "assertion", ("spatial_scope_id",)),
    ("idx_assertion_qualifier_unit_id", "assertion_qualifier", ("unit_id",)),
    (
        "idx_botanical_identification_decision_manual_species_entity_id",
        "botanical_identification_decision",
        ("manual_species_entity_id",),
    ),
    (
        "idx_botanical_identification_decision_validated_by_id",
        "botanical_identification_decision",
        ("validated_by_id",),
    ),
    ("idx_compliance_check_checked_by", "compliance_check", ("checked_by",)),
    ("idx_confidence_graph_computed_by", "confidence_graph", ("computed_by",)),
    ("idx_confidence_graph_valid_for_revision_id", "confidence_graph", ("valid_for_revision_id",)),
    ("idx_constraint_temporal_context_id", "constraint", ("temporal_context_id",)),
    ("idx_constraint_affected_recommendation_id", "constraint", ("affected_recommendation_id",)),
    ("idx_constraint_source_id", "constraint", ("source_id",)),
    ("idx_constraint_spatial_scope_id", "constraint", ("spatial_scope_id",)),
    ("idx_controlled_term_parent_id", "controlled_term", ("parent_id",)),
    ("idx_correlation_scale_context_id", "correlation", ("scale_context_id",)),
    ("idx_correlation_spatial_scope_id", "correlation", ("spatial_scope_id",)),
    ("idx_correlation_temporal_context_id", "correlation", ("temporal_context_id",)),
    ("idx_correlation_evidence_assessment_id", "correlation", ("evidence_assessment_id",)),
    ("idx_data_asset_archived_from", "data_asset", ("archived_from",)),
    ("idx_dataset_publisher_id", "dataset", ("publisher_id",)),
    ("idx_decision_question_id", "decision", ("question_id",)),
    ("idx_decision_scale_context_id", "decision", ("scale_context_id",)),
    ("idx_distribution_rights_statement_id", "distribution", ("rights_statement_id",)),
    ("idx_ecological_process_spatial_scope_id", "ecological_process", ("spatial_scope_id",)),
    ("idx_ecological_process_rate_unit_id", "ecological_process", ("rate_unit_id",)),
    ("idx_ecological_process_temporal_context_id", "ecological_process", ("temporal_context_id",)),
    ("idx_ecological_process_driver_phenomenon_id", "ecological_process", ("driver_phenomenon_id",)),
    ("idx_ecological_process_scale_context_id", "ecological_process", ("scale_context_id",)),
    ("idx_ecological_state_scale_context_id", "ecological_state", ("scale_context_id",)),
    ("idx_ecological_state_temporal_context_id", "ecological_state", ("temporal_context_id",)),
    ("idx_ecological_state_computed_by", "ecological_state", ("computed_by",)),
    ("idx_ecosystem_service_spatial_scope_id", "ecosystem_service", ("spatial_scope_id",)),
    ("idx_evidence_assessment_evaluator_id", "evidence_assessment", ("evaluator_id",)),
    ("idx_experiment_scale_context_id", "experiment", ("scale_context_id",)),
    ("idx_experiment_hypothesis_id", "experiment", ("hypothesis_id",)),
    ("idx_experiment_resulting_assertion_id", "experiment", ("resulting_assertion_id",)),
    ("idx_experiment_resulting_source_id", "experiment", ("resulting_source_id",)),
    ("idx_experiment_conducted_by", "experiment", ("conducted_by",)),
    ("idx_feature_unit_id", "feature", ("unit_id",)),
    ("idx_feature_set_model_version_id", "feature_set", ("model_version_id",)),
    ("idx_flow_uncertainty_id", "flow", ("uncertainty_id",)),
    ("idx_flow_temporal_context_id", "flow", ("temporal_context_id",)),
    ("idx_flow_magnitude_unit_id", "flow", ("magnitude_unit_id",)),
    ("idx_flow_scale_context_id", "flow", ("scale_context_id",)),
    ("idx_flow_driver_process_id", "flow", ("driver_process_id",)),
    ("idx_goal_scale_context_id", "goal", ("scale_context_id",)),
    ("idx_goal_temporal_context_id", "goal", ("temporal_context_id",)),
    ("idx_goal_parent_goal_id", "goal", ("parent_goal_id",)),
    ("idx_goal_spatial_scope_id", "goal", ("spatial_scope_id",)),
    ("idx_inference_input_snapshot_id", "inference", ("input_snapshot_id",)),
    ("idx_inference_output_assertion_id", "inference", ("output_assertion_id",)),
    ("idx_inference_feature_set_id", "inference", ("feature_set_id",)),
    ("idx_instance_spatial_scope_id", "instance", ("spatial_scope_id",)),
    ("idx_intervention_operator_id", "intervention", ("operator_id",)),
    ("idx_knowledge_lineage_confidence_graph_id", "knowledge_lineage", ("confidence_graph_id",)),
    ("idx_knowledge_lineage_produced_by", "knowledge_lineage", ("produced_by",)),
    ("idx_model_run_scenario_id", "model_run", ("scenario_id",)),
    ("idx_model_run_activity_id", "model_run", ("activity_id",)),
    ("idx_model_run_output_assertion_id", "model_run", ("output_assertion_id",)),
    ("idx_model_version_feature_set_id", "model_version", ("feature_set_id",)),
    ("idx_observation_instrument_id", "observation", ("instrument_id",)),
    ("idx_observation_feature_of_interest_id", "observation", ("feature_of_interest_id",)),
    ("idx_observation_temporal_context_id", "observation", ("temporal_context_id",)),
    ("idx_phenomenon_temporal_context_id", "phenomenon", ("temporal_context_id",)),
    ("idx_phenomenon_scale_context_id", "phenomenon", ("scale_context_id",)),
    ("idx_phenomenon_intensity_unit_id", "phenomenon", ("intensity_unit_id",)),
    ("idx_phenomenon_spatial_scope_id", "phenomenon", ("spatial_scope_id",)),
    ("idx_predicate_controlled_term_id", "predicate", ("controlled_term_id",)),
    ("idx_prov_entity_was_derived_from", "prov_entity", ("was_derived_from",)),
    ("idx_question_asked_by", "question", ("asked_by",)),
    ("idx_question_scale_context_id", "question", ("scale_context_id",)),
    ("idx_question_spatial_scope_id", "question", ("spatial_scope_id",)),
    ("idx_question_temporal_context_id", "question", ("temporal_context_id",)),
    ("idx_recommendation_recommended_by", "recommendation", ("recommended_by",)),
    ("idx_recommendation_question_id", "recommendation", ("question_id",)),
    ("idx_recommendation_scale_context_id", "recommendation", ("scale_context_id",)),
    ("idx_recommendation_spatial_scope_id", "recommendation", ("spatial_scope_id",)),
    ("idx_recommendation_temporal_context_id", "recommendation", ("temporal_context_id",)),
    ("idx_relation_type_parent_id", "relation_type", ("parent_id",)),
    ("idx_resource_diff_from_revision_id", "resource_diff", ("from_revision_id",)),
    ("idx_result_unit_id", "result", ("unit_id",)),
    ("idx_result_uncertainty_id", "result", ("uncertainty_id",)),
    ("idx_result_value_term_id", "result", ("value_term_id",)),
    ("idx_revision_activity_id", "revision", ("activity_id",)),
    ("idx_revision_parent_id", "revision", ("parent_id",)),
    ("idx_revision_author_id", "revision", ("author_id",)),
    ("idx_revision_diff_id", "revision", ("diff_id",)),
    ("idx_sample_collected_at", "sample", ("collected_at",)),
    ("idx_sample_sampling_event_id", "sample", ("sampling_event_id",)),
    ("idx_sampling_event_scale_context_id", "sampling_event", ("scale_context_id",)),
    ("idx_sampling_event_protocol_id", "sampling_event", ("protocol_id",)),
    ("idx_sampling_event_parent_event_id", "sampling_event", ("parent_event_id",)),
    (
        "idx_sampling_event_principal_investigator_id",
        "sampling_event",
        ("principal_investigator_id",),
    ),
    ("idx_sampling_event_temporal_context_id", "sampling_event", ("temporal_context_id",)),
    ("idx_scale_context_parent_scale_id", "scale_context", ("parent_scale_id",)),
    ("idx_scenario_scale_context_id", "scenario", ("scale_context_id",)),
    ("idx_scenario_temporal_context_id", "scenario", ("temporal_context_id",)),
    (
        "idx_sensitivity_classification_classified_by",
        "sensitivity_classification",
        ("classified_by",),
    ),
    ("idx_snapshot_revision_id", "snapshot", ("revision_id",)),
    ("idx_terrain_session_scale_context_id", "terrain_session", ("scale_context_id",)),
    ("idx_terrain_session_protocol_id", "terrain_session", ("protocol_id",)),
    ("idx_terrain_session_spatial_scope_id", "terrain_session", ("spatial_scope_id",)),
    ("idx_terrain_session_operator_id", "terrain_session", ("operator_id",)),
    ("idx_trait_definition_unit_id", "trait_definition", ("unit_id",)),
    ("idx_trait_value_uncertainty_id", "trait_value", ("uncertainty_id",)),
    ("idx_trait_value_observation_id", "trait_value", ("observation_id",)),
    ("idx_trait_value_scale_context_id", "trait_value", ("scale_context_id",)),
    ("idx_trait_value_value_term_id", "trait_value", ("value_term_id",)),
    ("idx_trait_value_unit_id", "trait_value", ("unit_id",)),
)

# CHECK constraints metier (P1-6) — bornes 0..1 sur les scores de
# confiance/probabilite, coherence temporelle, grandeurs physiques
# non negatives. Colonnes nullable : CHECK sur NULL est toujours
# satisfait (comportement standard SQL), aucune migration de donnees
# necessaire.
_CHECKS: tuple[tuple[str, str, str], ...] = (
    # (constraint_name, table_name, check_sql)
    ("chk_recommendation_confidence", "recommendation", "confidence >= 0 AND confidence <= 1"),
    ("chk_correlation_confidence", "correlation", "confidence >= 0 AND confidence <= 1"),
    ("chk_correlation_p_value", "correlation", "p_value >= 0 AND p_value <= 1"),
    ("chk_inference_confidence", "inference", "confidence >= 0 AND confidence <= 1"),
    (
        "chk_confidence_graph_score",
        "confidence_graph",
        "confidence_score >= 0 AND confidence_score <= 1",
    ),
    ("chk_management_plan_dates", "management_plan", "start_date <= end_date"),
    ("chk_intervention_area_ha", "intervention", "area_ha >= 0"),
    ("chk_intervention_volume_m3", "intervention", "volume_m3 >= 0"),
    ("chk_flow_magnitude", "flow", "magnitude >= 0"),
    (
        "chk_uncertainty_confidence_level",
        "uncertainty",
        "confidence_level >= 0 AND confidence_level <= 1",
    ),
    ("chk_quality_assessment_score", "quality_assessment", "score >= 0 AND score <= 1"),
    (
        "chk_ecological_state_overall_score",
        "ecological_state",
        "overall_score >= 0 AND overall_score <= 1",
    ),
)


def upgrade() -> None:
    # 1. Index FK
    for idx_name, table, cols in _INDEXES:
        op.create_index(idx_name, table, list(cols), if_not_exists=True)
    # 2. CHECK constraints
    for chk_name, table, check_sql in _CHECKS:
        op.create_check_constraint(chk_name, table, check_sql)


def downgrade() -> None:
    # 1. CHECK constraints (inverse)
    for chk_name, table, _ in reversed(_CHECKS):
        op.drop_constraint(chk_name, table, type_="check")
    # 2. Index FK (inverse)
    for idx_name, table, _ in reversed(_INDEXES):
        op.drop_index(idx_name, table_name=table, if_exists=True)
