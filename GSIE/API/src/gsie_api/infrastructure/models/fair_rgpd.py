"""Modèles FAIR/RGPD — types 62-65 (Sample, Consent, DataSubject, PersistentIdentifier)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    ConsentScope,
    LegalBasis,
    PIDType,
    SampleType,
)


@register_type("sample")
class SampleModel(Base, TimestampMixin):
    """Échantillon physique prélevé sur le terrain (mapping SOSA/SSN sosa:Sample)."""

    __tablename__ = "sample"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sample_type: Mapped[SampleType] = mapped_column(
        Enum(SampleType, name="sample_type"), nullable=False, index=True
    )
    sampling_event_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    material: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    storage_conditions: Mapped[str | None] = mapped_column(String(200), nullable=True)
    collected_at: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    mass_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_ml: Mapped[float | None] = mapped_column(Float, nullable=True)


@register_type("consent")
class ConsentModel(Base, TimestampMixin):
    """Consentement explicite RGPD d'une personne pour le traitement de ses données."""

    __tablename__ = "consent"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    data_subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[ConsentScope] = mapped_column(
        Enum(ConsentScope, name="consent_scope"),
        nullable=False,
        default=ConsentScope.full,
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    legal_basis: Mapped[LegalBasis] = mapped_column(
        Enum(LegalBasis, name="legal_basis"), nullable=False, index=True
    )
    document_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)


@register_type("data_subject")
class DataSubjectModel(Base, TimestampMixin):
    """Personne physique dont les données sont traitées (RGPD)."""

    __tablename__ = "data_subject"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    pseudonymized_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    email_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)
    anonymized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rights_exercised: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


@register_type("persistent_identifier")
class PersistentIdentifierModel(Base, TimestampMixin):
    """Identifiant persistant externe (DOI, ORCID, GBIF, Wikidata — FAIR F1)."""

    __tablename__ = "persistent_identifier"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    pid_type: Mapped[PIDType] = mapped_column(
        Enum(PIDType, name="pid_type"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    authority: Mapped[str] = mapped_column(String(100), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
