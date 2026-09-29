"""Persistance opérationnelle des analyses asynchrones GeoSylva."""

# ruff: noqa: TC003

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.accounts import IDENTITY_SCHEMA
from gsie_api.infrastructure.models.base import Base, TimestampMixin


class GeoSylvaAnalysisJobModel(Base, TimestampMixin):
    """Job mutable de pilotage ; la preuve scientifique reste `analysis_run`."""

    __tablename__ = "geosylva_analysis_job"
    __table_args__ = (
        UniqueConstraint("account_id", "request_id", name="uq_geosylva_analysis_account_request"),
        CheckConstraint(
            "status IN ('pending', 'running', 'partial', 'completed', 'failed', 'expired')",
            name="ck_geosylva_analysis_status",
        ),
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_geosylva_analysis_progress",
        ),
        CheckConstraint("attempt_count >= 0", name="ck_geosylva_analysis_attempts"),
        Index("ix_geosylva_analysis_account_status", "account_id", "status", "created_at"),
        Index("ix_geosylva_analysis_queue", "status", "next_attempt_at", "created_at"),
        Index("ix_geosylva_analysis_expiry", "expires_at"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    preparation_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    analysis_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    completed_engines: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    unavailable_engines: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String(100), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["GeoSylvaAnalysisJobModel"]
