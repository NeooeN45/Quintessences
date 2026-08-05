"""Modèle SQLAlchemy audit_log (journal d'audit append-only).

Schéma ``gsie_audit`` — introduit par la migration 20260803_0033.

Garanties append-only :
- Trigger ``prevent_audit_modification`` bloque UPDATE et DELETE côté DB.
- Rôle applicatif : ``GRANT SELECT, INSERT`` uniquement (REVOKE UPDATE, DELETE).
- RLS : visible par l'acteur lui-même ou par les admins.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base

AUDIT_SCHEMA = "gsie_audit"

_AUDIT_ACTIONS = (
    "'create', 'read', 'update', 'delete', 'export', "
    "'login', 'logout', 'invite', 'revoke', 'sync'"
)


class AuditLogModel(Base):
    """Entrée du journal d'audit — append-only (jamais modifiée ni supprimée)."""

    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint("action <> ''", name="ck_audit_log_action_non_empty"),
        CheckConstraint("resource_type <> ''", name="ck_audit_log_resource_type_non_empty"),
        CheckConstraint(f"action IN ({_AUDIT_ACTIONS})", name="ck_audit_log_action_enum"),
        Index("idx_audit_log_timestamp", text("timestamp DESC")),
        Index("idx_audit_log_actor", "actor_id"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_organisation", "organisation_id"),
        Index("idx_audit_log_action", "action"),
        {"schema": AUDIT_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    organisation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_organisations.organisation.id", ondelete="SET NULL"),
        nullable=True,
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_organisations.workspace.id", ondelete="SET NULL"),
        nullable=True,
    )
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(
        PGJSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
