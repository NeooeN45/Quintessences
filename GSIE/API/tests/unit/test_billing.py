"""Tests du catalogue et de la passerelle Stripe sans réseau externe."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from gsie_api.billing.service import BillingService, EntitlementRecord
from gsie_api.billing.stripe_gateway import (
    StripeBillingGateway,
    StripeNotConfiguredError,
    StripeWebhookError,
    StripeWebhookProcessor,
)
from gsie_api.core.config import get_settings


class FakeBillingRepository:
    async def list_public_plans(self) -> list[Any]:
        return []

    async def list_account_entitlements(self, account_id: UUID) -> list[EntitlementRecord]:
        return [
            EntitlementRecord("account.access", "account", account_id, "active", None),
            EntitlementRecord(
                "expired.feature",
                "account",
                account_id,
                "active",
                datetime.now(UTC) - timedelta(minutes=1),
            ),
        ]

    async def list_organisation_entitlements(
        self, organisation_id: UUID
    ) -> list[EntitlementRecord]:
        return [
            EntitlementRecord("enterprise.audit", "organisation", organisation_id, "active", None)
        ]

    async def ensure_free_account(self, account_id: UUID) -> None:
        return None


async def test_should_filter_expired_entitlements_when_context_is_resolved() -> None:
    account_id = uuid4()
    organisation_id = uuid4()
    service = BillingService(FakeBillingRepository())

    entitlements = await service.get_effective_entitlements(account_id, organisation_id)

    assert {item.feature_code for item in entitlements} == {
        "account.access",
        "enterprise.audit",
    }


def test_should_reject_checkout_when_stripe_is_disabled() -> None:
    gateway = StripeBillingGateway()

    with pytest.raises(StripeNotConfiguredError, match="Stripe n'est pas configuré"):
        gateway._configure()


def test_should_reject_webhook_when_stripe_is_disabled() -> None:
    processor = StripeWebhookProcessor.__new__(StripeWebhookProcessor)
    processor._settings = get_settings()

    with pytest.raises(StripeWebhookError, match="Webhook Stripe non configuré"):
        processor.parse_event(b"{}", None)
