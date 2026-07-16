"""Modèles écologie — types 43-49 (ScaleContext, Phenomenon, EcologicalProcess, etc.)."""

from uuid import UUID

from sqlalchemy import Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    EcologicalProcessType,
    PhenomenonType,
    RelationCategory,
    ScaleLevel,
)


@register_type("scale_context")
class ScaleContextModel(Base, TimestampMixin):
    """Contexte d'échelle écologique — toute corrélation dépend de l'échelle."""

    __tablename__ = "scale_context"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    level: Mapped[ScaleLevel] = mapped_column(
        Enum(ScaleLevel, name="scale_level"), nullable=False, index=True
    )
    parent_scale_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    extent_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    grain_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("phenomenon")
class PhenomenonModel(Base, TimestampMixin):
    """Phénomène écologique (sécheresse, tempête, attaque de scolytes, etc.)."""

    __tablename__ = "phenomenon"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    phenomenon_type: Mapped[PhenomenonType] = mapped_column(
        Enum(PhenomenonType, name="phenomenon_type"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    intensity: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity_unit_id: Mapped[UUID | None] = mapped_column(
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


@register_type("ecological_process")
class EcologicalProcessModel(Base, TimestampMixin):
    """Processus écologique (photosynthèse, croissance, décomposition, etc.)."""

    __tablename__ = "ecological_process"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    process_type: Mapped[EcologicalProcessType] = mapped_column(
        Enum(EcologicalProcessType, name="ecological_process_type"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    rate_unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    driver_phenomenon_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("relation_type")
class RelationTypeModel(Base, TimestampMixin):
    """Méta-classification des prédicats (causal, spatial, trophic, etc.)."""

    __tablename__ = "relation_type"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category: Mapped[RelationCategory] = mapped_column(
        Enum(RelationCategory, name="relation_category"),
        nullable=False, index=True,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("sampling_event")
class SamplingEventModel(Base, TimestampMixin):
    """Événement d'échantillonnage (campagne de terrain)."""

    __tablename__ = "sampling_event"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    protocol_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_design: Mapped[str] = mapped_column(Text, nullable=False)
    temporal_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    parent_event_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    principal_investigator_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("trait_definition")
class TraitDefinitionModel(Base, TimestampMixin):
    """Définition d'un trait fonctionnel (Leaf Area, SLA, Wood Density, etc.)."""

    __tablename__ = "trait_definition"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    abbreviation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    standard_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    value_range: Mapped[str | None] = mapped_column(String(100), nullable=True)


@register_type("trait_value")
class TraitValueModel(Base, TimestampMixin):
    """Valeur d'un trait pour une entité, avec incertitude et contexte."""

    __tablename__ = "trait_value"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    trait_definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_term_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    uncertainty_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    observation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
