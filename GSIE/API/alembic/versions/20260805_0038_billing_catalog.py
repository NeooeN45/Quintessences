"""Catalogue plans, abonnements et entitlements GSIE.

Cette migration ne connecte encore aucun prestataire de paiement. Elle crée la
source de vérité interne, indépendante de Stripe, Google Play et Apple.

Catalogue initial :
- free : accès de base
- geosylva_pro : 20 EUR/mois, GeoSylva uniquement
- quintessences_pro : 50 EUR/mois, bundle applicatif individuel
- enterprise : prix sur devis, organisation et fonctionnalités entreprise

Révision: 20260805_0038
Précède: 20260805_0037
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "20260805_0038"
down_revision: str | None = "20260805_0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "gsie_billing"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    op.create_table(
        "plan",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("product_scope", sa.String(64), nullable=False),
        sa.Column("monthly_amount_cents", sa.Integer, nullable=True),
        sa.Column("annual_amount_cents", sa.Integer, nullable=True),
        sa.Column("trial_days", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "monthly_amount_cents IS NULL OR monthly_amount_cents >= 0",
            name="ck_plan_monthly_amount",
        ),
        sa.CheckConstraint(
            "annual_amount_cents IS NULL OR annual_amount_cents >= 0", name="ck_plan_annual_amount"
        ),
        sa.CheckConstraint("trial_days >= 0 AND trial_days <= 90", name="ck_plan_trial_days"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_plan_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_plan_code"),
        schema=_SCHEMA,
    )

    op.create_table(
        "plan_feature",
        sa.Column("plan_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("feature_code", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["plan_id"], [f"{_SCHEMA}.plan.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_id", "feature_code"),
        schema=_SCHEMA,
    )

    op.create_table(
        "subscription",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("owner_type", sa.String(32), nullable=False),
        sa.Column("account_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("organisation_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("plan_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default=sa.text("'internal'")),
        sa.Column("external_subscription_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'trialing'")),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["gsie_rgpd_identites.user_account.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"], ["gsie_organisations.organisation.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["plan_id"], [f"{_SCHEMA}.plan.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "owner_type IN ('account', 'organisation')", name="ck_subscription_owner_type"
        ),
        sa.CheckConstraint(
            "(owner_type = 'account' AND account_id IS NOT NULL AND organisation_id IS NULL) OR "
            "(owner_type = 'organisation' AND organisation_id IS NOT NULL AND account_id IS NULL)",
            name="ck_subscription_single_owner",
        ),
        sa.CheckConstraint(
            "status IN ('trialing', 'active', 'past_due', 'canceled', 'unpaid', 'ended')",
            name="ck_subscription_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider", "external_subscription_id", name="uq_subscription_external"
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_subscription_account", "subscription", ["account_id", "status"], schema=_SCHEMA
    )
    op.create_index(
        "idx_subscription_organisation",
        "subscription",
        ["organisation_id", "status"],
        schema=_SCHEMA,
    )

    op.create_table(
        "entitlement",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(32), nullable=False),
        sa.Column("account_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("organisation_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("feature_code", sa.String(120), nullable=False),
        sa.Column("source_subscription_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "valid_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["gsie_rgpd_identites.user_account.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"], ["gsie_organisations.organisation.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["source_subscription_id"], [f"{_SCHEMA}.subscription.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "subject_type IN ('account', 'organisation')", name="ck_entitlement_subject_type"
        ),
        sa.CheckConstraint(
            "(subject_type = 'account' AND account_id IS NOT NULL AND organisation_id IS NULL) OR "
            "(subject_type = 'organisation' AND organisation_id IS NOT NULL AND account_id IS NULL)",
            name="ck_entitlement_single_subject",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'revoked', 'expired')", name="ck_entitlement_status"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subject_type",
            "account_id",
            "organisation_id",
            "feature_code",
            name="uq_entitlement_subject_feature",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_entitlement_account",
        "entitlement",
        ["account_id", "status", "feature_code"],
        schema=_SCHEMA,
    )
    op.create_index(
        "idx_entitlement_organisation",
        "entitlement",
        ["organisation_id", "status", "feature_code"],
        schema=_SCHEMA,
    )

    op.create_table(
        "billing_event",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("external_event_id", sa.String(255), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'received'")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_event_id", name="uq_billing_event_external"),
        schema=_SCHEMA,
    )

    op.execute(
        f"""
        INSERT INTO {_SCHEMA}.plan
            (id, code, display_name, product_scope, monthly_amount_cents, annual_amount_cents, trial_days)
        VALUES
            ('00000000-0000-0000-0000-000000000101', 'free', 'Free', 'basic', 0, NULL, 0),
            ('00000000-0000-0000-0000-000000000102', 'geosylva_pro', 'GeoSylva Pro', 'geosylva', 2000, NULL, 14),
            ('00000000-0000-0000-0000-000000000103', 'quintessences_pro', 'Quintessences Pro', 'all_apps', 5000, NULL, 14),
            ('00000000-0000-0000-0000-000000000104', 'enterprise', 'Enterprise', 'enterprise', NULL, NULL, 0)
        """
    )
    for table in ("plan", "plan_feature", "subscription", "entitlement"):
        op.execute(f"GRANT SELECT ON TABLE {_SCHEMA}.{table} TO gsie_application")
    op.execute(
        f"GRANT INSERT, UPDATE ON TABLE {_SCHEMA}.subscription, {_SCHEMA}.entitlement TO gsie_application"
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE {_SCHEMA}.billing_event TO gsie_application")
    op.execute(f"REVOKE DELETE ON ALL TABLES IN SCHEMA {_SCHEMA} FROM gsie_application")
    op.execute(f"ALTER TABLE {_SCHEMA}.subscription ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.subscription FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.entitlement ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_SCHEMA}.entitlement FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY subscription_scope_visible ON {_SCHEMA}.subscription
        USING (
            current_setting('app.billing_webhook', true) = 'true'
            OR account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR organisation_id = NULLIF(current_setting('app.current_organisation_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.billing_webhook', true) = 'true'
            OR account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR organisation_id = NULLIF(current_setting('app.current_organisation_id', true), '')::uuid
        )
        """
    )
    op.execute(
        f"""
        CREATE POLICY entitlement_scope_visible ON {_SCHEMA}.entitlement
        USING (
            current_setting('app.billing_webhook', true) = 'true'
            OR account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR organisation_id = NULLIF(current_setting('app.current_organisation_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.billing_webhook', true) = 'true'
            OR account_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR organisation_id = NULLIF(current_setting('app.current_organisation_id', true), '')::uuid
        )
        """
    )

    op.execute(
        f"""
        INSERT INTO {_SCHEMA}.plan_feature (plan_id, feature_code)
        VALUES
            ('00000000-0000-0000-0000-000000000101', 'account.access'),
            ('00000000-0000-0000-0000-000000000101', 'workspace.personal'),
            ('00000000-0000-0000-0000-000000000102', 'account.access'),
            ('00000000-0000-0000-0000-000000000102', 'workspace.personal'),
            ('00000000-0000-0000-0000-000000000102', 'geosylva.access'),
            ('00000000-0000-0000-0000-000000000102', 'geosylva.sync'),
            ('00000000-0000-0000-0000-000000000102', 'geosylva.advanced'),
            ('00000000-0000-0000-0000-000000000103', 'account.access'),
            ('00000000-0000-0000-0000-000000000103', 'workspace.personal'),
            ('00000000-0000-0000-0000-000000000103', 'geosylva.access'),
            ('00000000-0000-0000-0000-000000000103', 'geosylva.sync'),
            ('00000000-0000-0000-0000-000000000103', 'geosylva.advanced'),
            ('00000000-0000-0000-0000-000000000103', 'ignis.access'),
            ('00000000-0000-0000-0000-000000000103', 'artemis.access'),
            ('00000000-0000-0000-0000-000000000103', 'flora.access'),
            ('00000000-0000-0000-0000-000000000103', 'hydro.access'),
            ('00000000-0000-0000-0000-000000000104', 'account.access'),
            ('00000000-0000-0000-0000-000000000104', 'enterprise.sso'),
            ('00000000-0000-0000-0000-000000000104', 'enterprise.user_management'),
            ('00000000-0000-0000-0000-000000000104', 'enterprise.audit'),
            ('00000000-0000-0000-0000-000000000104', 'enterprise.security_policies'),
            ('00000000-0000-0000-0000-000000000104', 'hub.unreal'),
            ('00000000-0000-0000-0000-000000000104', 'all_apps.access')
        """
    )


def downgrade() -> None:
    op.drop_table("billing_event", schema=_SCHEMA)
    op.drop_table("entitlement", schema=_SCHEMA)
    op.drop_table("subscription", schema=_SCHEMA)
    op.drop_table("plan_feature", schema=_SCHEMA)
    op.drop_table("plan", schema=_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA}")
