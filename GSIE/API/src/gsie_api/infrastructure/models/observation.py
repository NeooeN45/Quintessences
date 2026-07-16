"""Modèles observation — types 14-19 (Observation, Result, Method, etc.)."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    QualityDimension,
    UncertaintyType,
    ValueType,
)


@register_type("observation")
class ObservationModel(Base, TimestampMixin):
    """Acte d'observer — porte sampling_effort et detection_probability."""

    __tablename__ = "observation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    feature_of_interest_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    method_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    instrument_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    sampling_effort: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    detection_probability: Mapped[float | None] = mapped_column(Float, nullable=True)


@register_type("result")
class ResultModel(Base, TimestampMixin):
    """Résultat d'une observation — value_type='absence' pour les absences."""

    __tablename__ = "result"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    observation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    value_type: Mapped[ValueType] = mapped_column(
        Enum(ValueType, name="value_type"), nullable=False
    )
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_term_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    uncertainty_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    detection_limit: Mapped[float | None] = mapped_column(Float, nullable=True)


@register_type("method")
class MethodModel(Base, TimestampMixin):
    """Méthode ou protocole d'observation/acquisition."""

    __tablename__ = "method"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    protocol_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


@register_type("instrument")
class InstrumentModel(Base, TimestampMixin):
    """Instrument ou capteur utilisé."""

    __tablename__ = "instrument"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    calibration_date: Mapped[date | None] = mapped_column(nullable=True)


@register_type("uncertainty")
class UncertaintyModel(Base, TimestampMixin):
    """Incertitude quantifiée sur un Result ou une Assertion."""

    __tablename__ = "uncertainty"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    type: Mapped[UncertaintyType] = mapped_column(
        Enum(UncertaintyType, name="uncertainty_type"), nullable=False
    )
    lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("quality_assessment")
class QualityAssessmentModel(Base, TimestampMixin):
    """Évaluation de qualité d'une donnée — FK vers resource.id."""

    __tablename__ = "quality_assessment"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    dimension: Mapped[QualityDimension] = mapped_column(
        Enum(QualityDimension, name="quality_dimension"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(200), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
