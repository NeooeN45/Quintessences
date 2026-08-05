"""Hardening auth — MFA TOTP, sessions actives, lockout, refresh reuse.

Introduit les tables manquantes pour un système d'authentification avancé :
- ``mfa_secret`` — secrets TOTP par compte (RFC 6238)
- ``mfa_recovery_code`` — codes de récupération à usage unique
- ``active_session`` — sessions JWT actives traquées par appareil
- ``failed_login_attempt`` — tentatives échouées pour lockout progressif
- ``revoked_refresh_token`` — refresh tokens révoqués pour détection de réutilisation

Révision: 20260803_0034
Précède: 20260803_0033
Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260803_0034"
down_revision: str | None = "20260803_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_rgpd_identites"


def upgrade() -> None:
    # --- Table mfa_secret : secret TOTP chiffré par compte ---
    op.create_table(
        "mfa_secret",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("secret_cipher", sa.String(500), nullable=False),
        sa.Column(
            "enabled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        {"schema": _SCHEMA},
    )
    op.create_index(
        "idx_mfa_secret_account",
        "mfa_secret",
        ["account_id"],
        schema=_SCHEMA,
    )

    # --- Table mfa_recovery_code : codes de récupération à usage unique ---
    op.create_table(
        "mfa_recovery_code",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(500), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", "code_hash", name="uq_mfa_recovery_code_account_hash"),
        {"schema": _SCHEMA},
    )
    op.create_index(
        "idx_mfa_recovery_code_account",
        "mfa_recovery_code",
        ["account_id"],
        schema=_SCHEMA,
    )

    # --- Table active_session : sessions JWT traquées par appareil ---
    op.create_table(
        "active_session",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("refresh_jti", sa.String(64), nullable=True, unique=True),
        sa.Column("device_name", sa.String(200), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column(
            "issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        {"schema": _SCHEMA},
    )
    op.create_index(
        "idx_active_session_account",
        "active_session",
        ["account_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_active_session_account_active",
        "active_session",
        ["account_id", "revoked_at"],
        schema=_SCHEMA,
    )

    # --- Table failed_login_attempt : lockout progressif ---
    op.create_table(
        "failed_login_attempt",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("email_normalized", sa.String(320), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column(
            "attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        {"schema": _SCHEMA},
    )
    op.create_index(
        "idx_failed_login_email_time",
        "failed_login_attempt",
        ["email_normalized", "attempted_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_failed_login_ip_time",
        "failed_login_attempt",
        ["ip_address", "attempted_at"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_failed_login_account_time",
        "failed_login_attempt",
        ["account_id", "attempted_at"],
        schema=_SCHEMA,
    )

    # --- Table revoked_refresh_token : détection de réutilisation ---
    op.create_table(
        "revoked_refresh_token",
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column(
            "account_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.user_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("reused_detected", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("reused_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("jti"),
        {"schema": _SCHEMA},
    )
    op.create_index(
        "idx_revoked_refresh_account",
        "revoked_refresh_token",
        ["account_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("revoked_refresh_token", schema=_SCHEMA)
    op.drop_table("failed_login_attempt", schema=_SCHEMA)
    op.drop_table("active_session", schema=_SCHEMA)
    op.drop_table("mfa_recovery_code", schema=_SCHEMA)
    op.drop_table("mfa_secret", schema=_SCHEMA)
