"""Tests du bootstrap explicite et de la campagne DatasetHealth fournisseur."""

from __future__ import annotations

import pytest

from gsie_api.data.adapters import AdapterContext
from gsie_api.data.bootstrap import (
    AdapterHealthService,
    build_adapter_registry,
    get_adapter_registry,
)
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


def test_default_registry_is_lazy_and_stable() -> None:
    registry = build_adapter_registry()

    assert [item.key for item in registry.descriptors()] == [
        "gbif",
        "ign",
        "meteofrance",
        "soilgrids",
    ]
    assert registry.get("GBIF") is registry.get("gbif")
    assert get_adapter_registry() is get_adapter_registry()


@pytest.mark.asyncio
async def test_offline_campaign_does_not_contact_providers() -> None:
    summary = await AdapterHealthService(build_adapter_registry()).check_all(
        trace_id="bootstrap-offline",
        offline=True,
    )

    assert len(summary.reports) == 4
    assert summary.healthy == 0
    assert summary.unavailable == 0
    assert summary.unknown == 4
    assert {item.error_code for item in summary.reports} == {"OFFLINE_MODE"}


@pytest.mark.asyncio
async def test_unexpected_adapter_failure_is_redacted() -> None:
    registry = build_adapter_registry()
    context = AdapterContext(trace_id="bootstrap-error", offline=False)

    class BrokenAdapter:
        descriptor = registry.descriptors()[0]

        async def health(self, context: AdapterContext) -> object:
            del context
            raise RuntimeError("secret-token-ne-doit-pas-sortir")

    registry.register_instance(BrokenAdapter(), replace=True)  # type: ignore[arg-type]
    report = await AdapterHealthService(registry).check_one("gbif", context=context)

    assert report.status is DatasetHealthStatus.unavailable
    assert report.error_code == "ADAPTER_HEALTH_CHECK_FAILED"
