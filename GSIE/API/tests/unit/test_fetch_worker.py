"""Tests fail-closed et streaming du worker FETCH borné."""

import asyncio
import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

from gsie_api.data.adapters import (
    AdapterContext,
    AdapterFetchRequest,
    AdapterFetchResult,
    AdapterSecurityError,
    DataSourceAdapter,
)
from gsie_api.data.fetch_policy import (
    FetchQualificationError,
    FetchQualificationRegistry,
    FetchSourceQualification,
    load_fetch_qualification,
)
from gsie_api.data.fetch_worker import BoundedFetchWorker

QUALIFICATION_PATH = Path(__file__).resolve().parents[3] / "DATASETS" / "FETCH_QUALIFICATION.json"


async def _body(*chunks: bytes, delay: float = 0) -> AsyncIterator[bytes]:
    for chunk in chunks:
        if delay:
            await asyncio.sleep(delay)
        yield chunk


def _qualified_registry(max_bytes: int = 1024) -> FetchQualificationRegistry:
    return FetchQualificationRegistry(
        schema_version="1",
        generated_at="2026-08-10",
        sources=[
            FetchSourceQualification(
                source_registry_id="soilgrids-wcs",
                status="qualified",
                fetch_enabled=True,
                legal_basis="SCI-001:OPEN_COPY",
                evidence_refs=["test-opérateur"],
                allowed_hosts=["maps.isric.org"],
                allowed_content_types=["image/tiff"],
                max_bytes=max_bytes,
                checksum_algorithm="sha256",
                reviewed_by="opérateur-test",
                reviewed_at=datetime.now(UTC),
            )
        ],
    )


def _adapter(result: AdapterFetchResult) -> DataSourceAdapter:
    return cast(
        "DataSourceAdapter",
        SimpleNamespace(
            supports=Mock(return_value=True),
            validate_target_url=Mock(return_value="https://maps.isric.org/mapserv"),
            fetch=AsyncMock(return_value=result),
        ),
    )


def _sink() -> SimpleNamespace:
    return SimpleNamespace(write=AsyncMock(), commit=AsyncMock(), abort=AsyncMock())


def _request(*, max_bytes: int = 1024, checksum: str | None = None) -> AdapterFetchRequest:
    return AdapterFetchRequest(
        external_id="phh2o_0-5cm_mean",
        distribution_url="https://maps.isric.org/mapserv",
        max_bytes=max_bytes,
        expected_checksum=checksum,
    )


@pytest.mark.asyncio
async def test_closed_source_never_calls_adapter() -> None:
    adapter = AsyncMock()
    sink = _sink()
    worker = BoundedFetchWorker(load_fetch_qualification(QUALIFICATION_PATH))

    with pytest.raises(FetchQualificationError, match="FETCH fermé"):
        await worker.fetch(
            source_registry_id="soilgrids-wcs",
            adapter=adapter,
            request=_request(),
            context=AdapterContext(trace_id="test-fetch"),
            sink=sink,
        )

    adapter.fetch.assert_not_awaited()
    sink.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_streams_and_commits_only_after_sha256_validation() -> None:
    payload = b"geotiff-test"
    checksum = hashlib.sha256(payload).hexdigest()
    adapter = _adapter(
        AdapterFetchResult(
            body=_body(payload), content_type="image/tiff", content_length=len(payload)
        )
    )
    sink = _sink()

    receipt = await BoundedFetchWorker(_qualified_registry()).fetch(
        source_registry_id="soilgrids-wcs",
        adapter=adapter,
        request=_request(checksum=checksum),
        context=AdapterContext(trace_id="fetch-ok", max_bytes=1024),
        sink=sink,
    )

    assert receipt.size_bytes == len(payload)
    assert receipt.checksum_sha256 == checksum
    sink.write.assert_awaited_once_with(payload)
    sink.commit.assert_awaited_once()
    sink.abort.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result",
    [
        AdapterFetchResult(body=_body(b"x"), content_type="text/html", content_length=1),
        AdapterFetchResult(body=_body(b"x"), content_type="image/tiff", content_length=2048),
        AdapterFetchResult(body=_body(b"x" * 700, b"y" * 700), content_type="image/tiff"),
    ],
)
async def test_rejects_unexpected_content_or_real_size_and_aborts(
    result: AdapterFetchResult,
) -> None:
    sink = _sink()

    with pytest.raises(AdapterSecurityError):
        await BoundedFetchWorker(_qualified_registry()).fetch(
            source_registry_id="soilgrids-wcs",
            adapter=_adapter(result),
            request=_request(),
            context=AdapterContext(trace_id="fetch-reject", max_bytes=1024),
            sink=sink,
        )

    sink.commit.assert_not_awaited()
    sink.abort.assert_awaited_once()


@pytest.mark.asyncio
async def test_checksum_mismatch_aborts_without_commit() -> None:
    sink = _sink()

    with pytest.raises(AdapterSecurityError, match="CHECKSUM_MISMATCH"):
        await BoundedFetchWorker(_qualified_registry()).fetch(
            source_registry_id="soilgrids-wcs",
            adapter=_adapter(AdapterFetchResult(body=_body(b"data"), content_type="image/tiff")),
            request=_request(checksum="0" * 64),
            context=AdapterContext(trace_id="fetch-checksum"),
            sink=sink,
        )

    sink.commit.assert_not_awaited()
    sink.abort.assert_awaited_once()


@pytest.mark.asyncio
async def test_total_timeout_aborts_storage() -> None:
    sink = _sink()

    with pytest.raises(AdapterSecurityError, match="FETCH_TIMEOUT"):
        await BoundedFetchWorker(_qualified_registry()).fetch(
            source_registry_id="soilgrids-wcs",
            adapter=_adapter(
                AdapterFetchResult(body=_body(b"data", delay=0.05), content_type="image/tiff")
            ),
            request=_request(),
            context=AdapterContext(trace_id="fetch-timeout", timeout_seconds=0.01),
            sink=sink,
        )

    sink.commit.assert_not_awaited()
    sink.abort.assert_awaited_once()


@pytest.mark.asyncio
async def test_abort_has_its_own_timeout() -> None:
    async def blocked_abort() -> None:
        await asyncio.sleep(1)

    sink = _sink()
    sink.abort = AsyncMock(side_effect=blocked_abort)

    with pytest.raises(AdapterSecurityError, match="FETCH_ABORT_TIMEOUT"):
        await BoundedFetchWorker(_qualified_registry(), abort_timeout_seconds=0.01).fetch(
            source_registry_id="soilgrids-wcs",
            adapter=_adapter(AdapterFetchResult(body=_body(b"data"), content_type="text/html")),
            request=_request(),
            context=AdapterContext(trace_id="fetch-abort-timeout"),
            sink=sink,
        )

    sink.commit.assert_not_awaited()
