"""Adapter SoilGrids WCS : tests hors réseau et contrôles de sécurité."""

from collections.abc import AsyncIterator

import pytest

from gsie_api.data.adapters import (
    AdapterContext,
    AdapterFetchRequest,
    AdapterFetchResult,
    AdapterQueryRequest,
    AdapterSecurityError,
)
from gsie_api.data.soilgrids_adapter import SoilGridsAdapter
from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClientError
from gsie_api.data.soilgrids_wcs_policy import SOILGRIDS_WCS_ENDPOINT, SoilGridsWcsRequest
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


async def _body(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


class FakeSoilGridsWcsClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.probe_calls = 0
        self.fetch_calls: list[tuple[SoilGridsWcsRequest, float]] = []

    async def probe(self) -> None:
        self.probe_calls += 1
        if self.fail:
            raise SoilGridsWcsClientError("erreur WCS SoilGrids simulée")

    async def fetch_coverage(
        self, request: SoilGridsWcsRequest, *, timeout_seconds: float, max_bytes: int
    ) -> AdapterFetchResult:
        if self.fail:
            raise SoilGridsWcsClientError("erreur WCS SoilGrids simulée")
        self.fetch_calls.append((request, timeout_seconds))
        return AdapterFetchResult(
            body=_body(b"geotiff-test"),
            content_type="image/tiff",
            content_length=12,
        )


def _parameters() -> dict[str, object]:
    return {
        "operation": "coverage",
        "property_code": "phh2o",
        "depth": "0-5cm",
        "quantile": "mean",
        "bbox": (-500.0, 1000.0, 0.0, 1500.0),
    }


@pytest.mark.asyncio
async def test_soilgrids_adapter_honore_le_mode_offline() -> None:
    client = FakeSoilGridsWcsClient()
    report = await SoilGridsAdapter(client).health(
        AdapterContext(trace_id="soil-offline", offline=True)
    )

    assert report.status is DatasetHealthStatus.unknown
    assert report.error_code == "OFFLINE_MODE"
    assert client.probe_calls == 0


@pytest.mark.asyncio
async def test_soilgrids_adapter_construit_une_requete_wcs_bornee() -> None:
    client = FakeSoilGridsWcsClient()
    adapter = SoilGridsAdapter(client)

    result = await adapter.query(
        AdapterQueryRequest(parameters=_parameters()),
        AdapterContext(trace_id="soil-query"),
    )

    item = result.items[0]
    assert item["source_registry_id"] == "soilgrids-wcs"
    assert item["coverage_id"] == "phh2o_0-5cm_mean"
    assert item["wcs_property_code"] == "phh2o"
    assert item["parameters"]["SERVICE"] == "WCS"
    assert item["parameters"]["FORMAT"] == "GEOTIFF_INT16"
    assert client.fetch_calls == []
    assert adapter.normalize(result)[0]["coverage_id"] == "phh2o_0-5cm_mean"


@pytest.mark.asyncio
async def test_soilgrids_adapter_fetch_transmet_une_requete_structuree() -> None:
    client = FakeSoilGridsWcsClient()
    request = AdapterFetchRequest(
        external_id="phh2o_0-5cm_mean",
        distribution_url=SOILGRIDS_WCS_ENDPOINT,
        max_bytes=1024,
        parameters=_parameters(),
    )

    result = await SoilGridsAdapter(client).fetch(
        request,
        AdapterContext(trace_id="soil-fetch", timeout_seconds=45.0),
    )

    assert b"".join([chunk async for chunk in result.body]) == b"geotiff-test"
    assert client.fetch_calls[0][0].coverage_id == "phh2o_0-5cm_mean"
    assert client.fetch_calls[0][1] == 30.0


@pytest.mark.asyncio
async def test_soilgrids_adapter_refuse_toujours_le_rest_beta() -> None:
    request = AdapterFetchRequest(
        external_id="phh2o_0-5cm_mean",
        distribution_url="https://rest.isric.org/soilgrids/v2.0",
        max_bytes=1024,
        parameters=_parameters(),
    )

    with pytest.raises(AdapterSecurityError, match="EGRESS_BLOCKED"):
        await SoilGridsAdapter(FakeSoilGridsWcsClient()).fetch(
            request,
            AdapterContext(trace_id="soil-rest"),
        )


@pytest.mark.asyncio
async def test_soilgrids_adapter_health_convertit_une_panne_en_statut_stable() -> None:
    report = await SoilGridsAdapter(FakeSoilGridsWcsClient(fail=True)).health(
        AdapterContext(trace_id="soil-health")
    )

    assert report.status is DatasetHealthStatus.unavailable
    assert report.error_code == "SOILGRIDS_WCS_HEALTH_CHECK_FAILED"
    assert report.latency_ms is not None


@pytest.mark.asyncio
async def test_soilgrids_adapter_refuse_les_parametres_invalides() -> None:
    adapter = SoilGridsAdapter(FakeSoilGridsWcsClient())
    context = AdapterContext(trace_id="soil-invalid")

    with pytest.raises(ValueError, match="propriété"):
        await adapter.query(
            AdapterQueryRequest(parameters={**_parameters(), "property_code": "unknown"}),
            context,
        )
    with pytest.raises(ValueError, match="emprise"):
        await adapter.query(
            AdapterQueryRequest(parameters={**_parameters(), "bbox": (0.0, 0.0, 0.0, 1.0)}),
            context,
        )
    with pytest.raises(ValueError, match="inconnue"):
        await adapter.query(AdapterQueryRequest(parameters={"operation": "unknown"}), context)


def test_soilgrids_descriptor_pointe_exclusivement_vers_le_wcs_allowliste() -> None:
    descriptor = SoilGridsAdapter(FakeSoilGridsWcsClient()).descriptor

    assert descriptor.key == "soilgrids"
    assert descriptor.version == "2.0.0"
    assert descriptor.domains == frozenset({"pedology", "soil_moisture"})
    assert descriptor.endpoint == SOILGRIDS_WCS_ENDPOINT
    assert descriptor.allowlisted_hosts == frozenset({"maps.isric.org"})
