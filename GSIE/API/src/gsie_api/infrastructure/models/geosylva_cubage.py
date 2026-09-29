"""Persistance des sessions de cubage synchronisées depuis GeoSylva."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.accounts import IDENTITY_SCHEMA
from gsie_api.infrastructure.models.base import Base, TimestampMixin


class GeoSylvaCubageSessionModel(Base, TimestampMixin):
    """Snapshot serveur immuable du paquet local de cubage."""

    __tablename__ = "geosylva_cubage_session"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "session_id",
            name="uq_geosylva_cubage_account_session",
        ),
        UniqueConstraint(
            "account_id",
            "idempotency_key",
            name="uq_geosylva_cubage_account_idempotency",
        ),
        CheckConstraint(
            "status IN ('accepted', 'synced', 'review_required', 'rejected', 'retryable_error')",
            name="ck_geosylva_cubage_status",
        ),
        Index("ix_geosylva_cubage_account_status", "account_id", "status", "created_at"),
        Index("ix_geosylva_cubage_calculation", "calculation_id"),
        {"schema": IDENTITY_SCHEMA},
    )

    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    calculation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    session_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    measurements_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    inputs_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="synced")
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    verification_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    trace_id: Mapped[str] = mapped_column(String(100), nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["GeoSylvaCubageSessionModel"]
