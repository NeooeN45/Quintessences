"""Modèles du catalogue de plans, abonnements et droits GSIE."""

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

from gsie_api.infrastructure.models.base import Base

BILLING_SCHEMA = "gsie_billing"


class PlanModel(Base):
    __tablename__ = "plan"
    __table_args__ = (
        CheckConstraint(
            "monthly_amount_cents IS NULL OR monthly_amount_cents >= 0",
            name="ck_plan_monthly_amount",
        ),
        CheckConstraint(
            "annual_amount_cents IS NULL OR annual_amount_cents >= 0", name="ck_plan_annual_amount"
        ),
        CheckConstraint("trial_days >= 0 AND trial_days <= 90", name="ck_plan_trial_days"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_plan_status"),
        UniqueConstraint("code", name="uq_plan_code"),
        {"schema": BILLING_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    product_scope: Mapped[str] = mapped_column(String(64), nullable=False)
    monthly_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annual_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trial_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PlanFeatureModel(Base):
    __tablename__ = "plan_feature"
    __table_args__ = ({"schema": BILLING_SCHEMA},)

    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{BILLING_SCHEMA}.plan.id", ondelete="CASCADE"),
        primary_key=True,
    )
    feature_code: Mapped[str] = mapped_column(String(120), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SubscriptionModel(Base):
    __tablename__ = "subscription"
    __table_args__ = (
        CheckConstraint(
            "owner_type IN ('account', 'organisation')", name="ck_subscription_owner_type"
        ),
        CheckConstraint(
            "(owner_type = 'account' AND account_id IS NOT NULL AND organisation_id IS NULL) OR "
            "(owner_type = 'organisation' AND organisation_id IS NOT NULL AND account_id IS NULL)",
            name="ck_subscription_single_owner",
        ),
        CheckConstraint(
            "status IN ('trialing', 'active', 'past_due', 'canceled', 'unpaid', 'ended')",
            name="ck_subscription_status",
        ),
        UniqueConstraint("provider", "external_subscription_id", name="uq_subscription_external"),
        Index("idx_subscription_account", "account_id", "status"),
        Index("idx_subscription_organisation", "organisation_id", "status"),
        {"schema": BILLING_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="CASCADE"),
        nullable=True,
    )
    organisation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_organisations.organisation.id", ondelete="CASCADE"),
        nullable=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{BILLING_SCHEMA}.plan.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'internal'")
    )
    external_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'trialing'")
    )
    trial_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EntitlementModel(Base):
    __tablename__ = "entitlement"
    __table_args__ = (
        CheckConstraint(
            "subject_type IN ('account', 'organisation')", name="ck_entitlement_subject_type"
        ),
        CheckConstraint(
            "(subject_type = 'account' AND account_id IS NOT NULL AND organisation_id IS NULL) OR "
            "(subject_type = 'organisation' AND organisation_id IS NOT NULL "
            "AND account_id IS NULL)",
            name="ck_entitlement_single_subject",
        ),
        CheckConstraint("status IN ('active', 'revoked', 'expired')", name="ck_entitlement_status"),
        UniqueConstraint(
            "subject_type",
            "account_id",
            "organisation_id",
            "feature_code",
            name="uq_entitlement_subject_feature",
        ),
        Index("idx_entitlement_account", "account_id", "status", "feature_code"),
        Index("idx_entitlement_organisation", "organisation_id", "status", "feature_code"),
        {"schema": BILLING_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_rgpd_identites.user_account.id", ondelete="CASCADE"),
        nullable=True,
    )
    organisation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gsie_organisations.organisation.id", ondelete="CASCADE"),
        nullable=True,
    )
    feature_code: Mapped[str] = mapped_column(String(120), nullable=False)
    source_subscription_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(f"{BILLING_SCHEMA}.subscription.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BillingEventModel(Base):
    __tablename__ = "billing_event"
    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_billing_event_external"),
        {"schema": BILLING_SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'received'")
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
