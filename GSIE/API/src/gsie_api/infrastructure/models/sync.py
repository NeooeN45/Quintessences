"""Répliques privées issues des applications mobiles Quintessences."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin

SYNC_SCHEMA = "gsie_synchronisation"


class GeoSylvaParcelSyncModel(Base, TimestampMixin):
    """Copie serveur versionnée ; une suppression reste sous forme de tombstone."""

    __tablename__ = "geosylva_parcels"
    __table_args__ = (
        UniqueConstraint("account_id", "client_id", name="uq_geosylva_parcels_owner_client"),
        CheckConstraint("server_version > 0", name="ck_geosylva_parcels_version"),
        Index("idx_geosylva_parcels_owner_updated", "account_id", "updated_at"),
        {"schema": SYNC_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    client_id: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    client_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    server_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_operation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
