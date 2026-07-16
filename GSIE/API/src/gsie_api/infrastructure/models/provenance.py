"""Modèles provenance — types 1-8 (Entity, EntityAlias, Concept, etc.)."""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type


@register_type("entity")
class EntityModel(Base, TimestampMixin):
    """Racine conceptuelle — tout objet avec identité, histoire ou relations."""

    __tablename__ = "entity"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_subtype: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)


@register_type("entity_alias")
class EntityAliasModel(Base, TimestampMixin):
    """Alias d'entité vers un référentiel externe (GBIF, INPN, TaxRef)."""

    __tablename__ = "entity_alias"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    namespace: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


@register_type("concept")
class ConceptModel(Base, TimestampMixin):
    """Concept stable et citable (ex. Quercus_robur)."""

    __tablename__ = "concept"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    preferred_label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    vocabulary_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )


@register_type("concept_version")
class ConceptVersionModel(Base, TimestampMixin):
    """Version d'un concept par release de vocabulaire."""

    __tablename__ = "concept_version"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    concept_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    release_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    fusions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


@register_type("vocabulary")
class VocabularyModel(Base, TimestampMixin):
    """Vocabulaire contrôlé (ex. TAXREF, WRB, EUR28)."""

    __tablename__ = "vocabulary"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    namespace: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)


@register_type("vocabulary_release")
class VocabularyReleaseModel(Base, TimestampMixin):
    """Release versionnée d'un vocabulaire."""

    __tablename__ = "vocabulary_release"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vocabulary_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)


@register_type("controlled_term")
class ControlledTermModel(Base, TimestampMixin):
    """Terme dans un vocabulaire, avec position hiérarchique optionnelle."""

    __tablename__ = "controlled_term"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vocabulary_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("instance")
class InstanceModel(Base, TimestampMixin):
    """Occurrence individuelle d'un Concept (ex. arbre n°458, placette A12)."""

    __tablename__ = "instance"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    concept_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    spatial_scope_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
