"""Modèles assertion — types 9-13 (Assertion, AssertionParticipant, etc.)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    ClaimKind,
    CitationRole,
    EvidenceLevel,
    LifecycleStatus,
    ParticipantRole,
    RuleSubtype,
)


@register_type("assertion")
class AssertionModel(Base, TimestampMixin):
    """Assertion scientifique unifiée — remplace KnowledgeObject (livrable 302)."""

    __tablename__ = "assertion"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    claim_kind: Mapped[ClaimKind] = mapped_column(
        Enum(ClaimKind, name="claim_kind"), nullable=False, index=True
    )
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False,
        index=True,
        default=LifecycleStatus.draft,
    )
    rule_subtype: Mapped[RuleSubtype | None] = mapped_column(
        Enum(RuleSubtype, name="rule_subtype"), nullable=True
    )
    predicate_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
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
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class AssertionParticipantModel(Base):
    """Participant typé à une assertion (sujet, objet, contexte)."""

    __tablename__ = "assertion_participant"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assertion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(ParticipantRole, name="participant_role"), nullable=False
    )
    participant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )


class AssertionQualifierModel(Base):
    """Qualificateur d'une assertion (région, période, métrique, protocole)."""

    __tablename__ = "assertion_qualifier"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assertion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("predicate")
class PredicateModel(Base, TimestampMixin):
    """Prédicat typé (ex. est_adapte_a, influence, contredit)."""

    __tablename__ = "predicate"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    inverse_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    controlled_term_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    relation_type_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )


@register_type("evidence_assessment")
class EvidenceAssessmentModel(Base, TimestampMixin):
    """Évaluation de preuve sur une assertion (multiples évaluations possibles)."""

    __tablename__ = "evidence_assessment"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assertion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    level: Mapped[EvidenceLevel] = mapped_column(
        Enum(EvidenceLevel, name="evidence_level"), nullable=False, index=True
    )
    evaluator_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    method: Mapped[str] = mapped_column(String(200), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
