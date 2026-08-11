"""Modèles IA/ML — types 31-36, 50-52 (Model, ModelRun, Dataset, Feature, etc.)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    AccessMethod,
    DatasetPurpose,
    DatasetStatus,
    EvidenceLevel,
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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    activity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    output_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    spatial_resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temporal_resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    purpose: Mapped[DatasetPurpose] = mapped_column(
        Enum(DatasetPurpose, name="dataset_purpose"),
        nullable=False,
        default=DatasetPurpose.production,
    )
    # Identité stable du Registry (RFC-0038 §5.2). Nullable pour les lignes
    # historiques découvertes avant la qualification ; le validateur impose
    # la présence dès qu'une entrée est promue.
    slug: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    primary_domain: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    domains: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)
    domain_vocabulary_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (UniqueConstraint("slug", name="uq_dataset_slug"),)


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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
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
    temporal_coverage_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    temporal_coverage_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    schema_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus, name="dataset_status"),
        nullable=False,
        default=DatasetStatus.discovered,
        index=True,
    )
    # Qualification Registry A–F, distincte des EvidenceAssessment d'assertion.
    evidence_level: Mapped[EvidenceLevel | None] = mapped_column(
        Enum(
            EvidenceLevel,
            name="evidence_level",
            values_callable=lambda values: [member.value for member in values],
        ),
        nullable=True,
    )
    evidence_basis: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    evidence_assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("dataset_id", "version", name="uq_dataset_version_dataset_version"),
        CheckConstraint(
            "temporal_coverage_start IS NULL OR temporal_coverage_end IS NULL "
            "OR temporal_coverage_start <= temporal_coverage_end",
            name="ck_dataset_version_coverage_order",
        ),
    )


@register_type("data_asset")
class DataAssetModel(Base, TimestampMixin):
    """Actif archivé via ``ObjectStorage`` — indépendance API (F-P2-08)."""

    __tablename__ = "data_asset"
    __table_args__ = (CheckConstraint("size_bytes >= 0", name="ck_data_asset_size_non_negative"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Un fichier de données peut dépasser 2 Gio : PostgreSQL INTEGER (32 bits)
    # n'est pas suffisant pour les COG, COPC ou archives de référence.
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(200), nullable=False)
    archived_from: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    original_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checksum_algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@register_type("distribution")
class DistributionModel(Base, TimestampMixin):
    """Distribution d'un DatasetVersion avec canal d'accès typé."""

    __tablename__ = "distribution"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "dataset_version_id",
            name="uq_distribution_id_dataset_version",
        ),
    )

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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    # Champ canonique RFC-0038 ; rights_statement_id est conservé pour les
    # lignes historiques RGPD et ne doit plus être utilisé pour une nouvelle
    # distribution qualifiée.
    data_rights_statement_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    coverage_place_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    format: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    crs: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    # Resolution native de la source (NOMENCLATURE_SOURCES.md §8.1).
    # `scale_context` porte deja `level`, `extent_m2` (couverture) et
    # `grain_m2` (resolution) : le rattacher ici evite de dupliquer la
    # resolution ailleurs, ce qui creerait deux sources de verite — faute
    # ecartee par DEC-000038 pour les regles.
    # Nullable : une distribution documentaire n'a pas de grain.
    scale_context_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id"),
        nullable=True,
        index=True,
        # `comment=` et non `doc=` : la migration pose un COMMENT ON COLUMN,
        # que PostgreSQL stocke. `doc` reste cote Python et laisserait le
        # modele diverger de la base.
        comment="Resolution native de la source, via scale_context.grain_m2",
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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    input_snapshot_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    output_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    inferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
