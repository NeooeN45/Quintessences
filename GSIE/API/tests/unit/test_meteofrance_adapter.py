"""Façade Météo-France : tests hors réseau avec un port fournisseur local."""

import pytest

from gsie_api.data.adapters import AdapterContext, AdapterQueryRequest
from gsie_api.data.meteofrance_adapter import MeteoFranceAdapter
from gsie_api.engines.climate.meteofrance_client import MeteoFranceClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


class FakeMeteoFranceClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    async def get_danger_feux_departements(self) -> list[dict[str, str | None]]:
        if self.fail:
            raise MeteoFranceClientError("erreur Météo-France simulée")
        self.calls += 1
        return [
            {
                "reference_time": "2026-08-10T00:00:00Z",
                "dep_code": "33",
                "niveau_j1": "2",
                "niveau_j2": None,
                "dep_nom": "Gironde",
            }
        ]


@pytest.mark.asyncio
async def test_meteofrance_adapter_honore_le_mode_offline() -> None:
    client = FakeMeteoFranceClient()
    report = await MeteoFranceAdapter(client).health(
        AdapterContext(trace_id="meteo-offline", offline=True)
    )

    assert report.status is DatasetHealthStatus.unknown
    assert report.error_code == "OFFLINE_MODE"
    assert client.calls == 0


@pytest.mark.asyncio
async def test_meteofrance_adapter_delegue_le_danger_de_feux() -> None:
    client = FakeMeteoFranceClient()
    adapter = MeteoFranceAdapter(client)

    result = await adapter.query(
        AdapterQueryRequest(parameters={"operation": "danger_feux_departements"}),
        AdapterContext(trace_id="meteo-query"),
    )

    assert result.items[0]["dep_code"] == "33"
    assert result.items[0]["niveau_j2"] is None
    assert client.calls == 1
    assert adapter.normalize(result)[0]["dep_nom"] == "Gironde"


@pytest.mark.asyncio
async def test_meteofrance_adapter_health_convertit_une_panne_en_statut_stable() -> None:
    report = await MeteoFranceAdapter(FakeMeteoFranceClient(fail=True)).health(
        AdapterContext(trace_id="meteo-health")
    )

    assert report.status is DatasetHealthStatus.unavailable
    assert report.error_code == "METEOFRANCE_HEALTH_CHECK_FAILED"
    assert report.latency_ms is not None


@pytest.mark.asyncio
async def test_meteofrance_adapter_refuse_les_operations_inconnues() -> None:
    adapter = MeteoFranceAdapter(FakeMeteoFranceClient())

    with pytest.raises(ValueError, match="inconnue"):
        await adapter.query(
            AdapterQueryRequest(parameters={"operation": "unknown"}),
            AdapterContext(trace_id="meteo-invalid"),
        )


def test_meteofrance_descriptor_est_explicitement_allowliste() -> None:
    descriptor = MeteoFranceAdapter(FakeMeteoFranceClient()).descriptor

    assert descriptor.key == "meteofrance"
    assert descriptor.domains == frozenset({"weather", "climate"})
    assert descriptor.endpoint == "https://public-api.meteofrance.fr/public/DPMeteoForets/v1"
    assert descriptor.allowlisted_hosts == frozenset({"public-api.meteofrance.fr"})
