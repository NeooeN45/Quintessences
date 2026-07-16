"""Modèles IA/ML — types 31-36, 50-52 (Model, ModelRun, Dataset, Feature, etc.)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    DatasetPurpose,
    FeatureSourceType,
    ModelType,
)


@register_type("model")
class ModelModel(Base, TimestampMixin):
    """Modèle scientifique ou IA (croissance, dynamique, propagation)."""

    __tablename__ = "model"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    type: Mapped[ModelType] = mapped_column(
        Enum(ModelType, name="model_type"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)


@register_type("model_run")
class ModelRunModel(Base, TimestampMixin):
    """Exécution d'un modèle."""

    __tablename__ = "model_run"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    model_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    scenario_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    activity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    output_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("dataset")
class DatasetModel(Base, TimestampMixin):
    """Jeu de données référencé — purpose précise l'usage (v6.2)."""

    __tablename__ = "dataset"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    publisher_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    spatial_resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temporal_resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    purpose: Mapped[DatasetPurpose] = mapped_column(
        Enum(DatasetPurpose, name="dataset_purpose"),
        nullable=False,
        default=DatasetPurpose.production,
    )


@register_type("model_version")
class ModelVersionModel(Base, TimestampMixin):
    """Version d'un modèle."""

    __tablename__ = "model_version"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    model_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(200), nullable=True)
    inputs_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    outputs_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    feature_set_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("dataset_version")
class DatasetVersionModel(Base, TimestampMixin):
    """Version d'un dataset."""

    __tablename__ = "dataset_version"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dataset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


@register_type("data_asset")
class DataAssetModel(Base, TimestampMixin):
    """Actif physique (fichier archivé localement) — indépendance API (F-P2-08)."""

    __tablename__ = "data_asset"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    checksum: Mapped[str] = mapped_column(String(200), nullable=False)
    archived_from: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    original_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@register_type("distribution")
class DistributionModel(Base, TimestampMixin):
    """Distribution d'un DatasetVersion avec canal d'accès typé."""

    __tablename__ = "distribution"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    access_method: Mapped[AccessMethod] = mapped_column(
        Enum(AccessMethod, name="access_method"), nullable=False, index=True
    )
    access_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    licence: Mapped[str] = mapped_column(String(100), nullable=False)
    rights_statement_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("feature")
class FeatureModel(Base, TimestampMixin):
    """Caractéristique calculée utilisée par les modèles IA."""

    __tablename__ = "feature"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[FeatureSourceType] = mapped_column(
        Enum(FeatureSourceType, name="feature_source_type"), nullable=False
    )
    computation_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("feature_set")
class FeatureSetModel(Base, TimestampMixin):
    """Collection structurée de Features pour entraîner/évaluer un modèle IA."""

    __tablename__ = "feature_set"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    model_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("inference")
class InferenceModel(Base, TimestampMixin):
    """Inférence produite par un modèle IA appliqué à de nouvelles données."""

    __tablename__ = "inference"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    model_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    feature_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    input_snapshot_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    output_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    inferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
