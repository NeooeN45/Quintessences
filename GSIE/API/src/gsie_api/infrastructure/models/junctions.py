"""Tables de jonction n:m — relations entre types du métamodèle v6.2.

17 tables de jonction pour les relations many-to-many explicitement
décrites dans le métamodèle. Ces tables ne sont pas des resources
(pas de @register_type) — elles sont des tables de liaison pures.
"""

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from gsie_api.infrastructure.models.base import Base

# 1. ModelRun (32) inputs — n:m vers resource.id
model_run_input = Table(
    "model_run_input",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "model_run_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("input_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Column("role", String(50), nullable=True),
    Index("ix_model_run_input_run", "model_run_id"),
    Index("ix_model_run_input_input", "input_id"),
)

# 2. ModelRun (32) outputs — n:m vers resource.id
model_run_output = Table(
    "model_run_output",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "model_run_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("output_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Column("role", String(50), nullable=True),
    Index("ix_model_run_output_run", "model_run_id"),
    Index("ix_model_run_output_output", "output_id"),
)

# 3. ConflictCluster (42) → Assertion
conflict_cluster_assertion = Table(
    "conflict_cluster_assertion",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "conflict_cluster_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("assertion_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_cc_assertion_cluster", "conflict_cluster_id"),
    Index("ix_cc_assertion_assertion", "assertion_id"),
)

# 4. Hypothesis (54) supporting_assertions → Assertion
hypothesis_supporting = Table(
    "hypothesis_supporting",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "hypothesis_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("assertion_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_hyp_supporting_hyp", "hypothesis_id"),
    Index("ix_hyp_supporting_assertion", "assertion_id"),
)

# 5. Hypothesis (54) contradicting_assertions → Assertion
hypothesis_contradicting = Table(
    "hypothesis_contradicting",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "hypothesis_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("assertion_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_hyp_contradicting_hyp", "hypothesis_id"),
    Index("ix_hyp_contradicting_assertion", "assertion_id"),
)

# 6. Decision (55) recommendations_considered → Recommendation
decision_recommendation = Table(
    "decision_recommendation",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "decision_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("recommendation_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_dec_rec_decision", "decision_id"),
    Index("ix_dec_rec_recommendation", "recommendation_id"),
)

# 7. Decision (55) evidence_refs → Citation
decision_evidence = Table(
    "decision_evidence",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "decision_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("citation_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_dec_evidence_decision", "decision_id"),
    Index("ix_dec_evidence_citation", "citation_id"),
)

# 8. Recommendation (56) supporting_assertions → Assertion
recommendation_assertion = Table(
    "recommendation_assertion",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "recommendation_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("assertion_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_rec_assertion_rec", "recommendation_id"),
    Index("ix_rec_assertion_assertion", "assertion_id"),
)

# 9. Recommendation (56) scenarios_evaluated → Scenario
recommendation_scenario = Table(
    "recommendation_scenario",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "recommendation_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("scenario_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_rec_scenario_rec", "recommendation_id"),
    Index("ix_rec_scenario_scenario", "scenario_id"),
)

# 10. FeatureSet (51) feature_ids → Feature
feature_set_feature = Table(
    "feature_set_feature",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "feature_set_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("feature_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_fs_feature_set", "feature_set_id"),
    Index("ix_fs_feature_feature", "feature_id"),
)

# 11. Experiment (71) scenario_ids → Scenario
experiment_scenario = Table(
    "experiment_scenario",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "experiment_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("scenario_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_exp_scenario_exp", "experiment_id"),
    Index("ix_exp_scenario_scenario", "scenario_id"),
)

# 12. Experiment (71) model_run_ids → ModelRun
experiment_model_run = Table(
    "experiment_model_run",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "experiment_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("model_run_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_exp_mr_exp", "experiment_id"),
    Index("ix_exp_mr_model_run", "model_run_id"),
)

# 13. EcologicalState (73) based_on → resource.id
ecological_state_basis = Table(
    "ecological_state_basis",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "ecological_state_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("basis_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Column("basis_type", String(50), nullable=True),
    Index("ix_eco_state_basis_state", "ecological_state_id"),
    Index("ix_eco_state_basis_basis", "basis_id"),
)

# 14. Correlation (58) variables → resource.id (avec role)
correlation_variable = Table(
    "correlation_variable",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "correlation_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("variable_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Column("role", String(50), nullable=True),
    Index("ix_corr_var_correlation", "correlation_id"),
    Index("ix_corr_var_variable", "variable_id"),
)

# 15. KnowledgeLineage (70) derived_from → resource.id (avec role)
knowledge_lineage_derived = Table(
    "knowledge_lineage_derived",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "knowledge_lineage_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("derived_from_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Column("role", String(50), nullable=True),  # primary_input, supporting_input, method
    Index("ix_kl_derived_lineage", "knowledge_lineage_id"),
    Index("ix_kl_derived_from", "derived_from_id"),
)

# 16. TerrainSession (72) sampling_event_ids → SamplingEvent
terrain_session_sampling = Table(
    "terrain_session_sampling",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "terrain_session_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("sampling_event_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_ts_sampling_session", "terrain_session_id"),
    Index("ix_ts_sampling_event", "sampling_event_id"),
)

# 17. TerrainSession (72) media_ids → Media
terrain_session_media = Table(
    "terrain_session_media",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "terrain_session_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("media_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_ts_media_session", "terrain_session_id"),
    Index("ix_ts_media_media", "media_id"),
)

# 18. DataSubject (64) consent_ids → Consent (n:m)
data_subject_consent = Table(
    "data_subject_consent",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "data_subject_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("consent_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Index("ix_ds_consent_subject", "data_subject_id"),
    Index("ix_ds_consent_consent", "consent_id"),
)

# 19. OutcomeTracking (79) evidence_ids → resource.id (observations, résultats)
# Trace les observations qui ont permis d'évaluer le résultat réel
outcome_evidence = Table(
    "outcome_evidence",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "outcome_id",
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("evidence_id", PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False),
    Column("role", String(50), nullable=False, default="supporting"),
    Index("ix_oe_outcome", "outcome_id"),
    Index("ix_oe_evidence", "evidence_id"),
)
