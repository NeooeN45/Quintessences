"""Intake isolé des observations et retours transmis par les applications."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin

FIELD_INTAKE_SCHEMA = "public"
FIELD_INTAKE_STATUSES = ("quarantined", "accepted", "rejected")


class FieldIntakeModel(Base, TimestampMixin):
    """Soumission applicative conservée en quarantaine avant qualification."""

    __tablename__ = "field_intake"
    __table_args__ = (
        UniqueConstraint(
            "application_key",
            "client_event_id",
            name="uq_field_intake_application_event",
        ),
        CheckConstraint(
            "status IN ('quarantined', 'accepted', 'rejected')",
            name="ck_field_intake_status",
        ),
        Index("ix_field_intake_submitted_by_received", "submitted_by", "received_at"),
        Index("ix_field_intake_status_received", "status", "received_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    submitted_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    application_key: Mapped[str] = mapped_column(String(100), nullable=False)
    client_event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="quarantined")
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    provenance: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    target_resource_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
