"""Modèles gouvernance — types 37-40, 42 (Rights, Access, Sensitivity, Conflict)."""

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    ConflictStatus,
    Permission,
    SensitivityLevel,
    UsageRights,
)


@register_type("rights_statement")
class RightsStatementModel(Base, TimestampMixin):
    """Déclaration de droits (licence, usage, restrictions)."""

    __tablename__ = "rights_statement"

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


@register_type("access_policy")
class AccessPolicyModel(Base, TimestampMixin):
    """Politique d'accès (qui peut lire, écrire, exporter)."""

    __tablename__ = "access_policy"

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
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )


@register_type("spatial_disclosure_policy")
class SpatialDisclosurePolicyModel(Base, TimestampMixin):
    """Politique de dégradation spatiale (maille 10km public, exact gestionnaire)."""

    __tablename__ = "spatial_disclosure_policy"

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
