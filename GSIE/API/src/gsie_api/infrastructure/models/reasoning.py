"""Modèles raisonnement — types 53-60 (Question, Hypothesis, Decision, etc.)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    CapabilityType,
    CorrelationMethod,
    CorrelationStrength,
    HypothesisStatus,
    LifecycleStatus,
    ProviderType,
    QuestionType,
    ScenarioSubtype,
    ScenarioType,
)


@register_type("question")
class QuestionModel(Base, TimestampMixin):
    """Question scientifique ou opérationnelle — point d'entrée du raisonnement."""

    __tablename__ = "question"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), nullable=False, index=True
    )
    asked_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("hypothesis")
class HypothesisModel(Base, TimestampMixin):
    """Hypothèse testable liée à une Question."""

    __tablename__ = "hypothesis"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[HypothesisStatus] = mapped_column(
        Enum(HypothesisStatus, name="hypothesis_status"),
        nullable=False, default=HypothesisStatus.proposed, index=True,
    )


@register_type("decision")
class DecisionModel(Base, TimestampMixin):
    """Décision prise par un humain (CON-001 — l'IA assiste, ne décide jamais)."""

    __tablename__ = "decision"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    decided_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    decision_text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("recommendation")
class RecommendationModel(Base, TimestampMixin):
    """Recommandation produite par un moteur GSIE — contournable (CON-001)."""

    __tablename__ = "recommendation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    recommended_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("scenario")
class ScenarioModel(Base, TimestampMixin):
    """Scénario (sylvicole, climatique, de gestion) pour ModelRuns et Recommendations."""

    __tablename__ = "scenario"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, name="scenario_type"), nullable=False, index=True
    )
    scenario_subtype: Mapped[ScenarioSubtype | None] = mapped_column(
        Enum(ScenarioSubtype, name="scenario_subtype"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("correlation")
class CorrelationModel(Base, TimestampMixin):
    """Corrélation entre entités/variables — versionné et évaluable."""

    __tablename__ = "correlation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    method: Mapped[CorrelationMethod] = mapped_column(
        Enum(CorrelationMethod, name="correlation_method"), nullable=False
    )
    coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    strength: Mapped[CorrelationStrength] = mapped_column(
        Enum(CorrelationStrength, name="correlation_strength"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_assessment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False, default=LifecycleStatus.draft,
    )


# EcosystemService (59) est défini dans dynamics.py (avec enum EcosystemServiceCategory)


@register_type("capability")
class CapabilityModel(Base, TimestampMixin):
    """Capacité d'un moteur ou d'une application (observer, predict, etc.)."""

    __tablename__ = "capability"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    capability_type: Mapped[CapabilityType] = mapped_column(
        Enum(CapabilityType, name="capability_type"), nullable=False, index=True
    )
    provider_type: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType, name="provider_type"), nullable=False
    )
    provider_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    input_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    output_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
