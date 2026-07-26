"""Outbox/Inbox pattern (ADR-005) — cohérence événementielle.

Outbox : events générés par l'API dans la même transaction que l'écriture DB.
Inbox : events reçus d'autres services (idempotence, déduplication).

Un worker séparé lit l'outbox et publie sur Redis Pub/Sub / WebSocket.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base

# Statuts d'un événement d'outbox.
OUTBOX_STATUS_PENDING = "pending"
OUTBOX_STATUS_PUBLISHED = "published"
OUTBOX_STATUS_DEAD_LETTER = "dead_letter"


class OutboxEvent(Base):
    """Outbox — event à publier (transactionnel avec l'écriture DB).

    `id` est aussi l'identifiant de l'événement diffusé (`event_id` du
    payload) : il ne change jamais, y compris après un rejeu. C'est ce qui
    rend la sémantique « au moins une fois » exploitable côté consommateur,
    qui peut dédupliquer sur cet identifiant.
    """

    __tablename__ = "outbox_event"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Statut : pending, published, dead_letter
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OUTBOX_STATUS_PENDING, index=True
    )

    # --- Reprise sur échec (P0 2026-07-26) ---
    # Nombre de tentatives de publication déjà consommées.
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    # Date d'éligibilité : un événement n'est resélectionné qu'à échéance.
    # C'est ce qui interdit la boucle de retry serrée et empêche un événement
    # empoisonné d'occuper indéfiniment la fenêtre de lot.
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    # Code d'erreur normalisé — jamais un message, jamais une traceback :
    # le payload d'un échec peut contenir une URL Redis ou un secret.
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Horodatage de mise en lettre morte, après épuisement des tentatives.
    dead_lettered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
        # Index de sélection du worker : statut + échéance.
        Index("ix_outbox_status_next_attempt", "status", "next_attempt_at"),
    )


class InboxEvent(Base):
    """Inbox — event reçu d'un autre service (idempotence)."""

    __tablename__ = "inbox_event"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
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

    __table_args__ = (Index("ix_inbox_source_external", "source", "external_id", unique=True),)
