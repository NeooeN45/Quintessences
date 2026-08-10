"""Modèles gouvernance — types 37-40, 42 (Rights, Access, Sensitivity, Conflict)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    ConflictStatus,
    DatasetHealthStatus,
    Permission,
    SensitivityLevel,
    UsageRights,
)


@register_type("rights_statement")
class RightsStatementModel(Base, TimestampMixin):
    """Déclaration de droits (licence, usage, restrictions)."""

    __tablename__ = "rights_statement"
    # Schema isole (RFC-0029 §4.2) : les declarations de droits sont des
    # politiques de controle d'acces — elles appartiennent au schema RGPD.
    __table_args__ = {"schema": "gsie_rgpd"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    licence: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    usage_rights: Mapped[UsageRights] = mapped_column(
        Enum(UsageRights, name="usage_rights"), nullable=False
    )
    attribution_required: Mapped[bool] = mapped_column(nullable=False, default=True)
    ai_training_allowed: Mapped[bool] = mapped_column(nullable=False, default=False)


@register_type("data_rights_statement")
class DataRightsStatementModel(Base, TimestampMixin):
    """Droits d'usage d'un dataset environnemental (RFC-0038 §5.4.1).

    Cette projection de gouvernance est distincte de ``RightsStatement``
    (schéma RGPD), afin qu'une licence ouverte ne donne jamais un accès
    implicite aux déclarations de données personnelles.
    """

    __tablename__ = "data_rights_statement"
    __table_args__ = {"schema": "gsie_gouvernance"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    licence: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    usage_rights: Mapped[UsageRights] = mapped_column(
        # Le type PostgreSQL usage_rights est déjà créé par la baseline.
        Enum(UsageRights, name="usage_rights"),
        nullable=False,
    )
    commercial_use_allowed: Mapped[bool] = mapped_column(nullable=False, default=False)
    redistribution_allowed: Mapped[bool] = mapped_column(nullable=False, default=False)
    attribution_required: Mapped[bool] = mapped_column(nullable=False, default=True)
    ai_training_allowed: Mapped[bool] = mapped_column(nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("dataset_health")
class DatasetHealthModel(Base, TimestampMixin):
    """Contrôle append-only de santé d'une distribution.

    ``distribution_id`` est obligatoire : un contrôle sans canal précis ne
    permettrait pas de distinguer l'indisponibilité d'une API de celle d'un
    asset archivé de la même version.
    """

    __tablename__ = "dataset_health"
    __table_args__ = (
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_dataset_health_latency"),
        CheckConstraint(
            "http_status IS NULL OR (http_status >= 100 AND http_status <= 599)",
            name="ck_dataset_health_http_status",
        ),
        ForeignKeyConstraint(
            ["distribution_id", "dataset_version_id"],
            ["distribution.id", "distribution.dataset_version_id"],
            name="fk_dataset_health_distribution_version",
        ),
        {"schema": "gsie_gouvernance"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    distribution_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    health_status: Mapped[DatasetHealthStatus] = mapped_column(
        Enum(DatasetHealthStatus, name="dataset_health_status"), nullable=False, index=True
    )
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observed_version: Mapped[str | None] = mapped_column(String(200), nullable=True)
    schema_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)


@register_type("access_policy")
class AccessPolicyModel(Base, TimestampMixin):
    """Politique d'accès (qui peut lire, écrire, exporter)."""

    __tablename__ = "access_policy"
    # Schema isole (RFC-0029 §4.2). Le registre doit declarer le meme
    # schema que la base, sinon le controle de derive strict voit la table
    # comme disparue de `public` et echoue pour une mauvaise raison.
    __table_args__ = {"schema": "gsie_rgpd"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    principal: Mapped[str] = mapped_column(String(200), nullable=False)
    permission: Mapped[Permission] = mapped_column(
        Enum(Permission, name="permission"), nullable=False, index=True
    )
    condition: Mapped[str | None] = mapped_column(Text, nullable=True)


@register_type("sensitivity_classification")
class SensitivityClassificationModel(Base, TimestampMixin):
    """Classification de sensibilité d'une donnée (ex. espèce protégée)."""

    __tablename__ = "sensitivity_classification"
    # Schema isole (RFC-0029 §4.2). Le registre doit declarer le meme
    # schema que la base, sinon le controle de derive strict voit la table
    # comme disparue de `public` et echoue pour une mauvaise raison.
    __table_args__ = {"schema": "gsie_rgpd"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    level: Mapped[SensitivityLevel] = mapped_column(
        Enum(SensitivityLevel, name="sensitivity_level"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    classified_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )


@register_type("spatial_disclosure_policy")
class SpatialDisclosurePolicyModel(Base, TimestampMixin):
    """Politique de dégradation spatiale (maille 10km public, exact gestionnaire)."""

    __tablename__ = "spatial_disclosure_policy"
    # Schema isole (RFC-0029 §4.2) : les politiques de divulgation spatiale
    # sont des politiques de controle d'acces — elles appartiennent au schema RGPD.
    __table_args__ = {"schema": "gsie_rgpd"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    public_precision: Mapped[str] = mapped_column(String(50), nullable=False)
    restricted_precision: Mapped[str] = mapped_column(String(50), nullable=False)
    authority: Mapped[str | None] = mapped_column(String(100), nullable=True)


@register_type("conflict_cluster")
class ConflictClusterModel(Base, TimestampMixin):
    """Groupe d'Assertions contradictoires (audit F-P2-05)."""

    __tablename__ = "conflict_cluster"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConflictStatus] = mapped_column(
        Enum(ConflictStatus, name="conflict_status"),
        nullable=False,
        default=ConflictStatus.open,
        index=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = {"schema": "gsie_gouvernance"}
