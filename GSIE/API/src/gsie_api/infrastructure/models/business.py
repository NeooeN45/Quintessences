"""Modèles métier forestier — types 74-79 (audit ONF/CNPF).

Types ajoutés pour rivaliser avec les systèmes de l'ONF et du CNPF :
- ManagementPlan (74) : plan d'aménagement / PSG
- Intervention (75) : intervention sylvicole programmée
- EconomicScenario (76) : dimension économique (coûts, valeur bois, aides)
- Regulation (77) + ComplianceCheck (78) : conformité réglementaire structurée
- OutcomeTracking (79) : suivi de résultat post-recommandation
- AdministrativeUnit (80) : unités administratives (forêt domaniale, triage, parcelle)

Source : audit externe 2026-07-16 — recommandation Fondateur.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    AdministrativeLevel,
    ComplianceStatus,
    EconomicCategory,
    InterventionStatus,
    InterventionType,
    ManagementPlanType,
    OutcomeStatus,
    PlanStatus,
    RegulationDomain,
)


@register_type("management_plan")
class ManagementPlanModel(Base, TimestampMixin):
    """Plan de gestion forestier pluriannuel (PSG CNPF / Aménagement ONF).

    Objet central du métier ONF/CNPF : engagement pluriannuel, daté, avec
    interventions programmées sur une parcelle donnée. Révisable.
    """

    __tablename__ = "management_plan"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    plan_type: Mapped[ManagementPlanType] = mapped_column(
        Enum(ManagementPlanType, name="management_plan_type"), nullable=False, index=True
    )
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status"),
        nullable=False,
        index=True,
        default=PlanStatus.draft,
    )
    spatial_scope_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    manager_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    approval_authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    objectives: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("intervention")
class InterventionModel(Base, TimestampMixin):
    """Intervention sylvicole programmée dans un plan de gestion.

    Ex. : éclaircie année N+5, coupe rase N+40, plantation, dépressage.
    """

    __tablename__ = "intervention"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    intervention_type: Mapped[InterventionType] = mapped_column(
        Enum(InterventionType, name="intervention_type"), nullable=False, index=True
    )
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, name="intervention_status"),
        nullable=False,
        index=True,
        default=InterventionStatus.planned,
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    spatial_scope_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_species: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    operator_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("economic_scenario")
class EconomicScenarioModel(Base, TimestampMixin):
    """Scénario économique — coûts, valeur bois, aides, rentabilité.

    L'ONF et le CNPF décident autant sur la rentabilité que sur l'écologie.
    Sans cette dimension, les recommandations sont hors-sol.
    """

    __tablename__ = "economic_scenario"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category: Mapped[EconomicCategory] = mapped_column(
        Enum(EconomicCategory, name="economic_category"), nullable=False, index=True
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    intervention_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    amount_eur: Mapped[float] = mapped_column(Float, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


@register_type("regulation")
class RegulationModel(Base, TimestampMixin):
    """Réglementation structurée et vérifiable machine.

    Code forestier, obligations PSG, Natura 2000 — pas juste du texte libre.
    Permet une chaîne Regulation → ComplianceCheck interrogeable.
    """

    __tablename__ = "regulation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    domain: Mapped[RegulationDomain] = mapped_column(
        Enum(RegulationDomain, name="regulation_domain"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    penalties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


@register_type("compliance_check")
class ComplianceCheckModel(Base, TimestampMixin):
    """Vérification de conformité d'une action/plan face à une réglementation.

    Permet de répondre : "ce plan est-il conforme au code forestier ?"
    """

    __tablename__ = "compliance_check"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    regulation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus, name="compliance_status"),
        nullable=False,
        index=True,
        default=ComplianceStatus.pending_check,
    )
    checked_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    waiver_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("outcome_tracking")
class OutcomeTrackingModel(Base, TimestampMixin):
    """Suivi de résultat post-recommandation — bouclage de validation.

    "Cette Recommendation a été suivie, voici ce qui s'est réellement
    passé 5 ans après." Sans cet objet, impossible de prouver empiriquement
    que le système est meilleur que l'expertise humaine.
    """

    __tablename__ = "outcome_tracking"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    recommendation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    decision_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    status: Mapped[OutcomeStatus] = mapped_column(
        Enum(OutcomeStatus, name="outcome_status"),
        nullable=False,
        index=True,
        default=OutcomeStatus.pending,
    )
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    actual_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    recalibration_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("administrative_unit")
class AdministrativeUnitModel(Base, TimestampMixin):
    """Unité administrative réelle (forêt domaniale, triage, parcelle cadastrale).

    Pont entre la hiérarchie écologique (ScaleContext) et la hiérarchie
    juridique/cadastrale. Nécessaire pour interopérer avec les données
    ONF/CNPF réelles.
    """

    __tablename__ = "administrative_unit"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    level: Mapped[AdministrativeLevel] = mapped_column(
        Enum(AdministrativeLevel, name="administrative_level"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
