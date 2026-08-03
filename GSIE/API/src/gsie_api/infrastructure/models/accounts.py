"""Comptes et moyens de connexion Quintessences (RFC-0032)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
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

IDENTITY_SCHEMA = "gsie_rgpd_identites"


class UserAccountModel(Base, TimestampMixin):
    """Compte canonique commun à toutes les applications Quintessences."""

    __tablename__ = "user_account"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'disabled', 'pending_deletion')",
            name="ck_user_account_status",
        ),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IdentityProviderLinkModel(Base, TimestampMixin):
    """Lien révocable entre un compte et une identité locale ou externe."""

    __tablename__ = "identity_provider_link"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "issuer",
            "subject",
            name="uq_identity_provider_link_provider_issuer_subject",
        ),
        CheckConstraint(
            "provider IN ('local', 'google', 'oidc', 'saml')",
            name="ck_identity_provider_link_provider",
        ),
        Index("idx_identity_provider_link_account", "account_id"),
        Index("idx_identity_provider_link_email", "email_normalized"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(320), nullable=False)
    email_normalized: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    last_authenticated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LocalCredentialModel(Base):
    """Secret dérivé Argon2id d'un lien d'identité local."""

    __tablename__ = "local_credential"
    __table_args__ = ({"schema": IDENTITY_SCHEMA},)

    identity_link_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.identity_provider_link.id", ondelete="CASCADE"),
        primary_key=True,
    )
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AccountRoleModel(Base):
    """Rôle Quintessences borné par un périmètre applicatif."""

    __tablename__ = "account_role"
    __table_args__ = (
        CheckConstraint("role <> ''", name="ck_account_role_non_empty"),
        CheckConstraint("application <> ''", name="ck_account_role_application_non_empty"),
        {"schema": IDENTITY_SCHEMA},
    )

    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        primary_key=True,
    )
    application: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default="quintessences",
        server_default=text("'quintessences'"),
    )
    role: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
