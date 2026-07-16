"""Modèles dynamiques — types 66-73 (Flow, ConfidenceGraph, Goal, Constraint, etc.)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    ConstraintSeverity,
    ConstraintType,
    EcologicalGrade,
    EcosystemServiceCategory,
    FlowDirection,
    FlowType,
    GoalPriority,
    GoalType,
    PropagationMethod,
    StateType,
    SyncStatus,
    TerrainSessionType,
    Trend,
)


@register_type("flow")
class FlowModel(Base, TimestampMixin):
    """Flux écologique entre compartiments (carbone, eau, nutriments, etc.)."""

    __tablename__ = "flow"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    flow_type: Mapped[FlowType] = mapped_column(
        Enum(FlowType, name="flow_type"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    sink_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    magnitude: Mapped[float] = mapped_column(Float, nullable=False)
    magnitude_unit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    direction: Mapped[FlowDirection] = mapped_column(
        Enum(FlowDirection, name="flow_direction"),
        nullable=False, default=FlowDirection.source_to_sink,
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    driver_process_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    uncertainty_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("confidence_graph")
class ConfidenceGraphModel(Base, TimestampMixin):
    """Graphe de confiance — propage l'incertitude à travers la chaîne."""

    __tablename__ = "confidence_graph"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    root_resource_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    propagation_method: Mapped[PropagationMethod] = mapped_column(
        Enum(PropagationMethod, name="propagation_method"), nullable=False
    )
    source_nodes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    propagation_tree: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    computed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    valid_for_revision_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("revision.id"), nullable=True
    )


@register_type("goal")
class GoalModel(Base, TimestampMixin):
    """Objectif de gestion (biodiversité, production, risque, conservation)."""

    __tablename__ = "goal"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    goal_type: Mapped[GoalType] = mapped_column(
        Enum(GoalType, name="goal_type"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[GoalPriority] = mapped_column(
        Enum(GoalPriority, name="goal_priority"),
        nullable=False, default=GoalPriority.secondary,
    )
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    parent_goal_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    success_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("constraint")
class ConstraintModel(Base, TimestampMixin):
    """Contrainte qui limite les recommandations réalisables."""

    __tablename__ = "constraint"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    constraint_type: Mapped[ConstraintType] = mapped_column(
        Enum(ConstraintType, name="constraint_type"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[ConstraintSeverity] = mapped_column(
        Enum(ConstraintSeverity, name="constraint_severity"),
        nullable=False, default=ConstraintSeverity.limiting,
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    affected_recommendation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("knowledge_lineage")
class KnowledgeLineageModel(Base, TimestampMixin):
    """Nœud explicite du DAG de lignage de connaissance (A → B → Recommendation)."""

    __tablename__ = "knowledge_lineage"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    produced_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    production_method: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    confidence_graph_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    lineage_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@register_type("experiment")
class ExperimentModel(Base, TimestampMixin):
    """Série d'expérimentations groupant plusieurs ModelRuns avec comparaison."""

    __tablename__ = "experiment"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    hypothesis_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    comparison_metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    resulting_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    resulting_source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    conducted_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("terrain_session")
class TerrainSessionModel(Base, TimestampMixin):
    """Mission terrain GeoSylva — météo, GPS, matériel, photos, LiDAR."""

    __tablename__ = "terrain_session"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    session_type: Mapped[TerrainSessionType] = mapped_column(
        Enum(TerrainSessionType, name="terrain_session_type"),
        nullable=False, index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    weather: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    gps_precision_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    equipment: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    protocol_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    sync_status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, name="sync_status"),
        nullable=False, default=SyncStatus.pending,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("ecological_state")
class EcologicalStateModel(Base, TimestampMixin):
    """État écologique synthétique d'un écosystème (santé, vitalité, risque)."""

    __tablename__ = "ecological_state"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    spatial_scope_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    state_type: Mapped[StateType] = mapped_column(
        Enum(StateType, name="state_type"), nullable=False, index=True
    )
    indicators: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_grade: Mapped[EcologicalGrade | None] = mapped_column(
        Enum(EcologicalGrade, name="ecological_grade"), nullable=True
    )
    computed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    trend: Mapped[Trend | None] = mapped_column(
        Enum(Trend, name="trend"), nullable=True
    )


@register_type("ecosystem_service")
class EcosystemServiceModel(Base, TimestampMixin):
    """Service écosystémique (régulation, support, production, culture)."""

    __tablename__ = "ecosystem_service"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    category: Mapped[EcosystemServiceCategory] = mapped_column(
        Enum(EcosystemServiceCategory, name="ecosystem_service_category"),
        nullable=False, index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
