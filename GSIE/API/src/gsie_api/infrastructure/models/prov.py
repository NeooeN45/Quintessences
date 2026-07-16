"""Modèles PROV-O — types 20-24 (Activity, ProvEntity, Agent, Source, Citation)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    ActivityType,
    AgentType,
    CitationRole,
    SourceNature,
    SourceSubtype,
)


@register_type("activity")
class ActivityModel(Base, TimestampMixin):
    """Activité PROV — transformation, extraction, ingestion, validation."""

    __tablename__ = "activity"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, name="activity_type"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    agent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    method_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("prov_entity")
class ProvEntityModel(Base, TimestampMixin):
    """Entité PROV — artefact produit ou consommé par une Activity."""

    __tablename__ = "prov_entity"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    checksum: Mapped[str | None] = mapped_column(String(200), nullable=True)
    checksum_algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    was_derived_from: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    was_generated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )


@register_type("agent")
class AgentModel(Base, TimestampMixin):
    """Agent PROV — personne, organisation, logiciel."""

    __tablename__ = "agent"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, name="agent_type"), nullable=False, index=True
    )
    orcid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ror: Mapped[str | None] = mapped_column(String(50), nullable=True)


@register_type("source")
class SourceModel(Base, TimestampMixin):
    """Source d'information — porte source_nature (data vs knowledge provider)."""

    __tablename__ = "source"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtype: Mapped[SourceSubtype] = mapped_column(
        Enum(SourceSubtype, name="source_subtype"), nullable=False, index=True
    )
    source_nature: Mapped[SourceNature] = mapped_column(
        Enum(SourceNature, name="source_nature"), nullable=False, index=True
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    licence: Mapped[str | None] = mapped_column(String(100), nullable=True)


@register_type("citation")
class CitationModel(Base, TimestampMixin):
    """Citation d'une Source par une Assertion ou Observation."""

    __tablename__ = "citation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    citation_role: Mapped[CitationRole] = mapped_column(
        Enum(CitationRole, name="citation_role"), nullable=False
    )
    locator: Mapped[str | None] = mapped_column(String(100), nullable=True)
