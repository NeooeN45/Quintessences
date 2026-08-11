"""Organisations, workspaces et appartenance (multi-tenant enterprise).

Schéma ``gsie_organisations`` — introduit par la migration 20260803_0032.

- ``OrganisationModel`` — entité racine possédée par un compte créateur.
- ``WorkspaceModel`` — sous-ensemble d'une organisation (périmètre de travail).
- ``OrganisationMemberModel`` — appartenance compte ↔ organisation avec rôle.

Row Level Security (DEC-000037) :
- ``organisation`` visible par créateur ou membre (fonction ``is_member``).
- ``workspace`` visible si l'organisation parente est visible.
- ``organisation_member`` visible par le compte lui-même ou le créateur de l'org.
- ``REVOKE DELETE`` sur les trois tables (soft delete via ``deleted_at``).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin

ORGANISATIONS_SCHEMA = "gsie_organisations"


class OrganisationModel(Base, TimestampMixin):
    """Entité racine du multi-tenant GSIE — possédée par un compte créateur."""

    __tablename__ = "organisation"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_organisation_status"),
        CheckConstraint("slug <> ''", name="ck_organisation_slug_non_empty"),
        CheckConstraint("display_name <> ''", name="ck_organisation_display_name_non_empty"),
        UniqueConstraint("slug", name="uq_organisation_slug"),
        Index("idx_organisation_created_by", "created_by"),
        {"schema": ORGANISATIONS_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkspaceModel(Base, TimestampMixin):
    """Sous-ensemble d'une organisation — périmètre de travail isolé."""

    __tablename__ = "workspace"
    __table_args__ = (
        CheckConstraint("slug <> ''", name="ck_workspace_slug_non_empty"),
        CheckConstraint("display_name <> ''", name="ck_workspace_display_name_non_empty"),
        UniqueConstraint("organisation_id", "slug", name="uq_workspace_org_slug"),
        Index("idx_workspace_organisation", "organisation_id"),
        {"schema": ORGANISATIONS_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organisation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{ORGANISATIONS_SCHEMA}.organisation.id", ondelete="CASCADE"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrganisationInvitationModel(Base):
    """Invitation e-mail à usage unique vers une organisation."""

    __tablename__ = "organisation_invitation"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'member')",
            name="ck_organisation_invitation_role",
        ),
        UniqueConstraint("token_hash", name="uq_organisation_invitation_token_hash"),
        Index("idx_organisation_invitation_org", "organisation_id", "created_at"),
        Index("idx_organisation_invitation_email", "email_normalized", "expires_at"),
        {"schema": ORGANISATIONS_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organisation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{ORGANISATIONS_SCHEMA}.organisation.id", ondelete="CASCADE"),
        nullable=False,
    )
    email_normalized: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="member", server_default=text("'member'")
    )
    invited_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OrganisationMemberModel(Base):
    """Appartenance compte ↔ organisation avec rôle (owner/admin/member)."""

    __tablename__ = "organisation_member"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_organisation_member_role"),
        Index("idx_organisation_member_account", "account_id"),
        {"schema": ORGANISATIONS_SCHEMA},
    )

    organisation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{ORGANISATIONS_SCHEMA}.organisation.id", ondelete="CASCADE"),
        primary_key=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="member",
        server_default=text("'member'"),
    )
    invited_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
