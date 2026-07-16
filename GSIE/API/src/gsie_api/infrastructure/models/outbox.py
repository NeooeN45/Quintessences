"""Outbox/Inbox pattern (ADR-005) — cohérence événementielle.

Outbox : events générés par l'API dans la même transaction que l'écriture DB.
Inbox : events reçus d'autres services (idempotence, déduplication).

Un worker séparé lit l'outbox et publie sur Redis Pub/Sub / WebSocket.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base


class OutboxEvent(Base):
    """Outbox — event à publier (transactionnel avec l'écriture DB)."""

    __tablename__ = "outbox_event"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Statut : pending, published, failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
    )


class InboxEvent(Base):
    """Inbox — event reçu d'un autre service (idempotence)."""

    __tablename__ = "inbox_event"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Statut : received, processed, failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="received", index=True)

    __table_args__ = (
        Index("ix_inbox_source_external", "source", "external_id", unique=True),
    )
