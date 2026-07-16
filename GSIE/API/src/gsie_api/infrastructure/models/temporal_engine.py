"""Modèles Temporal Engine — types 29, 30, 61 (Revision, Snapshot, ResourceDiff).

GSIE Temporal & Provenance Engine (ADR-002) — bitemporel + PROV-O.
Revision et Snapshot sont des tables internes (pas des resources).
ResourceDiff est une resource (peut être référencée).
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type


class RevisionModel(Base):
    """Révision universelle d'une ressource — append-only (CON-010).

    Bitemporelle : valid_time (quand c'est vrai) + transaction_time (immuable).
    """

    __tablename__ = "revision"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("revision.id"), nullable=True)
    valid_time_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_time_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    diff_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    __table_args__ = (Index("ix_revision_target_version", "target_id", "version"),)


class SnapshotModel(Base):
    """Instantané immuable d'un état complet pour reproductibilité."""

    __tablename__ = "snapshot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("revision.id"), nullable=True
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    serialized_state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    checksum: Mapped[str] = mapped_column(String(200), nullable=False)


@register_type("resource_diff")
class ResourceDiffModel(Base, TimestampMixin):
    """Différentiel explicite entre deux Revisions (ADR-002).

    Documente ce qui a changé : champs ajoutés, modifiés, supprimés,
    relations ajoutées/retirées. Permet à un humain ou un moteur de
    comprendre l'évolution sans comparer deux snapshots complets.
    """

    __tablename__ = "resource_diff"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    from_revision_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("revision.id"), nullable=True
    )
    to_revision_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("revision.id"), nullable=True, index=True
    )
    changes: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="{added: {...}, modified: {field: {from, to}}, removed: {...}}",
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Champs legacy pour compatibilité service (field_changes, added/removed_relations)
    field_changes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    added_relations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    removed_relations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
