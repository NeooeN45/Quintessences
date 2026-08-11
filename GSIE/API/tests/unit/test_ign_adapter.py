"""Façade IGN : tests hors réseau avec un port fournisseur local."""

import pytest

from gsie_api.data.adapters import AdapterContext, AdapterQueryRequest
from gsie_api.data.ign_adapter import IGNAdapter
from gsie_api.engines.gis.ign_client import IGNClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


class FakeIGNClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.altitude_calls: list[tuple[float, float]] = []
        self.parcelle_calls: list[tuple[str, str, str]] = []

    async def get_altitude(self, latitude: float, longitude: float) -> float:
        if self.fail:
            raise IGNClientError("erreur IGN simulée")
        self.altitude_calls.append((latitude, longitude))
        return 42.5

    async def get_parcelle(
        self, code_insee: str, section: str, numero: str
    ) -> dict[str, object] | None:
        if self.fail:
            raise IGNClientError("erreur IGN simulée")
        self.parcelle_calls.append((code_insee, section, numero))
        return {"type": "Feature", "id": f"{section}-{numero}"}


@pytest.mark.asyncio
async def test_ign_adapter_honore_le_mode_offline() -> None:
    client = FakeIGNClient()
    report = await IGNAdapter(client).health(AdapterContext(trace_id="ign-offline", offline=True))

    assert report.status is DatasetHealthStatus.unknown
    assert report.error_code == "OFFLINE_MODE"
    assert client.altitude_calls == []


@pytest.mark.asyncio
async def test_ign_adapter_delegue_altitude_et_cadastre() -> None:
    client = FakeIGNClient()
    adapter = IGNAdapter(client)
    context = AdapterContext(trace_id="ign-query")

    altitude = await adapter.query(
        AdapterQueryRequest(
            parameters={
                "operation": "altitude",
                "latitude": 45.0,
                "longitude": 2.0,
            }
        ),
        context,
    )
    parcelle = await adapter.query(
        AdapterQueryRequest(
            parameters={
                "operation": "parcelle",
                "code_insee": "75056",
                "section": "AB",
                "numero": "12",
            }
        ),
        context,
    )

    assert altitude.items[0]["altitude_m"] == 42.5
    assert parcelle.items[0]["id"] == "AB-12"
    assert client.altitude_calls == [(45.0, 2.0)]
    assert client.parcelle_calls == [("75056", "AB", "12")]
    assert adapter.normalize(altitude)[0]["latitude"] == 45.0


@pytest.mark.asyncio
async def test_ign_adapter_health_convertit_une_panne_en_statut_stable() -> None:
    report = await IGNAdapter(FakeIGNClient(fail=True)).health(
        AdapterContext(trace_id="ign-health")
    )

    assert report.status is DatasetHealthStatus.unavailable
    assert report.error_code == "IGN_HEALTH_CHECK_FAILED"
    assert report.latency_ms is not None


@pytest.mark.asyncio
async def test_ign_adapter_refuse_les_parametres_invalides() -> None:
    adapter = IGNAdapter(FakeIGNClient())
    context = AdapterContext(trace_id="ign-invalid")

    with pytest.raises(ValueError, match="latitude"):
        await adapter.query(
            AdapterQueryRequest(
                parameters={"operation": "altitude", "latitude": 95, "longitude": 2}
            ),
            context,
        )
    with pytest.raises(ValueError, match="code_insee"):
        await adapter.query(
            AdapterQueryRequest(
                parameters={
                    "operation": "parcelle",
                    "code_insee": "",
                    "section": "AB",
                    "numero": "1",
                }
            ),
            context,
        )
    with pytest.raises(ValueError, match="inconnue"):
        await adapter.query(AdapterQueryRequest(parameters={"operation": "unknown"}), context)


def test_ign_descriptor_couvre_les_deux_hotes_avec_un_endpoint_public() -> None:
    descriptor = IGNAdapter(FakeIGNClient()).descriptor

    assert descriptor.key == "ign"
    assert descriptor.domains == frozenset({"gis", "elevation"})
    assert descriptor.endpoint == "https://apicarto.ign.fr/api/cadastre/parcelle"
    assert descriptor.allowlisted_hosts == frozenset({"apicarto.ign.fr", "data.geopf.fr"})
