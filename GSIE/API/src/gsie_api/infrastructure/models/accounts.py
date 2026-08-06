"""Comptes et moyens de connexion Quintessences (RFC-0032)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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
        CheckConstraint("session_version > 0", name="ck_user_account_session_version"),
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
    session_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deletion_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


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


class IdentityActionTokenModel(Base):
    """Code à usage unique pour vérifier l'adresse ou restaurer le compte."""

    __tablename__ = "identity_action_token"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('verify_email', 'reset_password')",
            name="ck_identity_action_token_purpose",
        ),
        Index(
            "idx_identity_action_token_active",
            "account_id",
            "purpose",
            "consumed_at",
        ),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AccountConsentModel(Base):
    """Consentement juridique versionné et révocable."""

    __tablename__ = "account_consent"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "consent_type",
            "document_version",
            name="uq_account_consent_version",
        ),
        Index("idx_account_consent_active", "account_id", "consent_type", "revoked_at"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    consent_type: Mapped[str] = mapped_column(String(64), nullable=False)
    document_version: Mapped[str] = mapped_column(String(32), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class EmailChangeRequestModel(Base):
    """Demande de changement e-mail nécessitant deux confirmations."""

    __tablename__ = "email_change_request"
    __table_args__ = (
        Index("idx_email_change_request_active", "account_id", "completed_at", "expires_at"),
        Index("idx_email_change_request_new_email", "new_email_normalized", "completed_at"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_email_normalized: Mapped[str] = mapped_column(String(320), nullable=False)
    new_email_normalized: Mapped[str] = mapped_column(String(320), nullable=False)
    current_code_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    new_code_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    current_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    new_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MfaSecretModel(Base):
    """Secret TOTP chiffré associé à un compte (RFC 6238)."""

    __tablename__ = "mfa_secret"
    __table_args__ = (
        Index("idx_mfa_secret_account", "account_id"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    secret_cipher: Mapped[str] = mapped_column(String(500), nullable=False)
    enabled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MfaRecoveryCodeModel(Base):
    """Code de récupération MFA à usage unique, hashé Argon2."""

    __tablename__ = "mfa_recovery_code"
    __table_args__ = (
        UniqueConstraint("account_id", "code_hash", name="uq_mfa_recovery_code_account_hash"),
        Index("idx_mfa_recovery_code_account", "account_id"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    code_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ActiveSessionModel(Base):
    """Session JWT active traquée par appareil pour révocation sélective."""

    __tablename__ = "active_session"
    __table_args__ = (
        Index("idx_active_session_account", "account_id"),
        Index("idx_active_session_account_active", "account_id", "revoked_at"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    refresh_jti: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FailedLoginAttemptModel(Base):
    """Tentative de connexion échouée pour lockout progressif."""

    __tablename__ = "failed_login_attempt"
    __table_args__ = (
        Index("idx_failed_login_email_time", "email_normalized", "attempted_at"),
        Index("idx_failed_login_ip_time", "ip_address", "attempted_at"),
        Index("idx_failed_login_account_time", "account_id", "attempted_at"),
        {"schema": IDENTITY_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=True,
    )
    email_normalized: Mapped[str | None] = mapped_column(String(320), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RevokedRefreshTokenModel(Base):
    """Refresh token révoqué pour détection de réutilisation."""

    __tablename__ = "revoked_refresh_token"
    __table_args__ = (
        Index("idx_revoked_refresh_account", "account_id"),
        {"schema": IDENTITY_SCHEMA},
    )

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{IDENTITY_SCHEMA}.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reused_detected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    reused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
