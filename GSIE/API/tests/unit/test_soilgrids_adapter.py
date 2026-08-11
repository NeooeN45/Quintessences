"""Façade SoilGrids : tests hors réseau avec un port fournisseur local."""

import pytest

from gsie_api.data.adapters import AdapterContext, AdapterQueryRequest
from gsie_api.data.soilgrids_adapter import SoilGridsAdapter
from gsie_api.engines.pedology.soilgrids_client import SoilGridsClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


class FakeSoilGridsClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[float, float, list[str], str]] = []

    async def get_properties(
        self, latitude: float, longitude: float, properties: list[str], depth: str = "0-5cm"
    ) -> dict[str, float]:
        if self.fail:
            raise SoilGridsClientError("erreur SoilGrids simulée")
        self.calls.append((latitude, longitude, properties, depth))
        return {"phh2o": 5.4, "clay": 28.3}

    @staticmethod
    def unit_for(property_name: str) -> str:
        return "pH" if property_name == "phh2o" else "%"


@pytest.mark.asyncio
async def test_soilgrids_adapter_honore_le_mode_offline() -> None:
    client = FakeSoilGridsClient()
    report = await SoilGridsAdapter(client).health(
        AdapterContext(trace_id="soil-offline", offline=True)
    )

    assert report.status is DatasetHealthStatus.unknown
    assert report.error_code == "OFFLINE_MODE"
    assert client.calls == []


@pytest.mark.asyncio
async def test_soilgrids_adapter_delegue_les_proprietes_et_conserve_les_valeurs() -> None:
    client = FakeSoilGridsClient()
    adapter = SoilGridsAdapter(client)

    result = await adapter.query(
        AdapterQueryRequest(
            parameters={
                "operation": "properties",
                "latitude": 45.0,
                "longitude": 2.0,
                "properties": ["phh2o", "clay"],
                "depth": "0-5cm",
            }
        ),
        AdapterContext(trace_id="soil-query"),
    )

    assert result.items[0]["phh2o"] == 5.4
    assert result.items[0]["clay"] == 28.3
    assert client.calls == [(45.0, 2.0, ["phh2o", "clay"], "0-5cm")]
    assert adapter.normalize(result)[0]["phh2o"] == 5.4


@pytest.mark.asyncio
async def test_soilgrids_adapter_health_convertit_une_panne_en_statut_stable() -> None:
    report = await SoilGridsAdapter(FakeSoilGridsClient(fail=True)).health(
        AdapterContext(trace_id="soil-health")
    )

    assert report.status is DatasetHealthStatus.unavailable
    assert report.error_code == "SOILGRIDS_HEALTH_CHECK_FAILED"
    assert report.latency_ms is not None


@pytest.mark.asyncio
async def test_soilgrids_adapter_refuse_les_parametres_invalides() -> None:
    adapter = SoilGridsAdapter(FakeSoilGridsClient())
    context = AdapterContext(trace_id="soil-invalid")

    with pytest.raises(ValueError, match="properties"):
        await adapter.query(
            AdapterQueryRequest(
                parameters={
                    "operation": "properties",
                    "latitude": 45,
                    "longitude": 2,
                    "properties": [],
                }
            ),
            context,
        )
    with pytest.raises(ValueError, match="latitude"):
        await adapter.query(
            AdapterQueryRequest(
                parameters={
                    "operation": "properties",
                    "latitude": 100,
                    "longitude": 2,
                    "properties": ["phh2o"],
                }
            ),
            context,
        )
    with pytest.raises(ValueError, match="inconnue"):
        await adapter.query(AdapterQueryRequest(parameters={"operation": "unknown"}), context)


def test_soilgrids_descriptor_est_explicitement_allowliste() -> None:
    descriptor = SoilGridsAdapter(FakeSoilGridsClient()).descriptor

    assert descriptor.key == "soilgrids"
    assert descriptor.domains == frozenset({"pedology", "soil_moisture"})
    assert descriptor.endpoint == "https://rest.isric.org/soilgrids/v2.0/properties/query"
    assert descriptor.allowlisted_hosts == frozenset({"rest.isric.org"})
