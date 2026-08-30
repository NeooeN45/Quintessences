"""Tests du scheduler distribué de santé Data Registry."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from gsie_api.core.config import Settings
from gsie_api.data.adapters import AdapterHealthReport
from gsie_api.data.health_scheduler import (
    DataRegistryHealthScheduler,
    _resolve_manifest_slug,
    snapshot_from_report,
)
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


class FakeRedis:
    def __init__(self, *, acquired: bool) -> None:
        self.acquired = acquired
        self.set_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.eval_calls: list[tuple[Any, ...]] = []

    async def set(self, *args: Any, **kwargs: Any) -> bool:
        self.set_calls.append((args, kwargs))
        return self.acquired

    async def eval(self, *args: Any) -> int:
        self.eval_calls.append(args)
        return 1


def _settings() -> Settings:
    return cast(
        Settings,
        SimpleNamespace(
            data_registry_health_lock_ttl_seconds=600,
            data_registry_health_interval_seconds=3600.0,
        ),
    )


@pytest.mark.asyncio
async def test_run_once_skips_when_distributed_lock_is_held() -> None:
    scheduler = DataRegistryHealthScheduler(_settings())
    scheduler._collect_and_persist = AsyncMock()  # type: ignore[method-assign]
    redis = FakeRedis(acquired=False)

    assert await scheduler.run_once(cast(Any, redis)) is False
    scheduler._collect_and_persist.assert_not_awaited()
    assert redis.set_calls[0][1] == {"nx": True, "ex": 600}
    assert redis.eval_calls == []


@pytest.mark.asyncio
async def test_run_once_releases_owned_lock_after_persistence() -> None:
    scheduler = DataRegistryHealthScheduler(_settings())
    scheduler._collect_and_persist = AsyncMock()  # type: ignore[method-assign]
    redis = FakeRedis(acquired=True)

    assert await scheduler.run_once(cast(Any, redis)) is True
    scheduler._collect_and_persist.assert_awaited_once()
    assert len(redis.eval_calls) == 1
    assert redis.eval_calls[0][1] == 1


@pytest.mark.asyncio
async def test_run_once_releases_lock_when_collection_fails() -> None:
    scheduler = DataRegistryHealthScheduler(_settings())
    scheduler._collect_and_persist = AsyncMock(  # type: ignore[method-assign]
        side_effect=RuntimeError("incident fournisseur")
    )
    redis = FakeRedis(acquired=True)

    with pytest.raises(RuntimeError, match="incident fournisseur"):
        await scheduler.run_once(cast(Any, redis))
    assert len(redis.eval_calls) == 1


def test_snapshot_preserves_operational_health_fields() -> None:
    checked_at = datetime.now(UTC)
    report = AdapterHealthReport(
        adapter_key="gbif",
        status=DatasetHealthStatus.healthy,
        checked_at=checked_at,
        latency_ms=12.5,
        http_status=200,
        observed_version="v1",
    )

    snapshot = snapshot_from_report(report)

    assert snapshot.checked_at == checked_at
    assert snapshot.health_status is DatasetHealthStatus.healthy
    assert snapshot.latency_ms == 12.5
    assert snapshot.http_status == 200


def test_health_scheduler_prefers_canonical_manifest_slug() -> None:
    assert (
        _resolve_manifest_slug("gbif", {"gbif-species-api", "gbif-occurrences"})
        == "gbif-species-api"
    )


def test_health_scheduler_keeps_historical_slug_as_read_only_fallback() -> None:
    assert _resolve_manifest_slug("gbif", {"gbif-occurrences"}) == "gbif-occurrences"


def test_health_scheduler_ne_cible_jamais_le_rest_beta_soilgrids() -> None:
    assert (
        _resolve_manifest_slug("soilgrids", {"soilgrids-rest-beta", "soilgrids-wcs"})
        == "soilgrids-wcs"
    )
    assert _resolve_manifest_slug("soilgrids", {"soilgrids-rest-beta"}) is None


def test_health_scheduler_rejects_unknown_adapter_projection() -> None:
    assert _resolve_manifest_slug("unknown", {"gbif-species-api"}) is None
