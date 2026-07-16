"""Modèles spatial/temporal — types 25-28 (Unit, Place, TemporalContext, Media)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import MediaType, TemporalGranularity


@register_type("unit")
class UnitModel(Base, TimestampMixin):
    """Unité de mesure (UCUM/QUDT)."""

    __tablename__ = "unit"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ucum_code: Mapped[str | None] = mapped_column(String(50), nullable=True)


@register_type("place")
class PlaceModel(Base, TimestampMixin):
    """Entité spatiale — PostGIS pour la géométrie (SRID 2154 Lambert-93)."""

    __tablename__ = "place"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    geometry: Mapped[Any] = mapped_column(
        Geometry("GEOMETRY", srid=2154, spatial_index=True),
        nullable=True,
    )
    srid: Mapped[int] = mapped_column(Integer, nullable=False, default=2154)
    label: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)


@register_type("temporal_context")
class TemporalContextModel(Base, TimestampMixin):
    """Contexte temporel bitemporel — implémenté via le Temporal Engine."""

    __tablename__ = "temporal_context"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    valid_time_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_time_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_time_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    transaction_time_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    granularity: Mapped[TemporalGranularity] = mapped_column(
        Enum(TemporalGranularity, name="temporal_granularity"), nullable=False
    )


@register_type("media")
class MediaModel(Base, TimestampMixin):
    """Média associé (photo, audio, vidéo, document)."""

    __tablename__ = "media"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="media_type"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(200), nullable=True)
