"""Contrats publics du catalogue et des entitlements GSIE."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    display_name: str
    product_scope: str
    monthly_amount_cents: int | None
    annual_amount_cents: int | None
    trial_days: int
    features: list[str]


class PlanListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plans: list[PlanResponse]


class EntitlementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_code: str
    subject_type: str
    subject_id: UUID
    status: str
    valid_until: datetime | None


class BillingContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID
    organisation_id: UUID | None
    features: list[str]
    entitlements: list[EntitlementResponse]


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_code: str
    owner_type: str = "account"


class CheckoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkout_url: str


class UpgradeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_plan_code: str


class BillingOperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool = True


class StorePurchaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purchase_token: str


class StorePurchaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    plan_code: str
    status: str
    expires_at: datetime | None
