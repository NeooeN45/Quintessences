"""Façade GBIF : aucun appel réseau dans les tests."""

import pytest

from gsie_api.data.adapters import AdapterContext, AdapterQueryRequest
from gsie_api.data.gbif_adapter import GBIFAdapter
from gsie_api.engines.botanical.gbif_client import GBIFClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


class FakeGBIFClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.match_calls: list[str] = []
        self.vernacular_calls: list[tuple[int, str]] = []

    async def match_species(self, name: str) -> dict[str, object] | None:
        if self.fail:
            raise GBIFClientError("erreur réseau simulée")
        self.match_calls.append(name)
        return {"usageKey": 123, "scientificName": name}

    async def get_vernacular_name(self, taxon_key: int, language: str = "fra") -> str | None:
        self.vernacular_calls.append((taxon_key, language))
        return "Chêne pédonculé"


@pytest.mark.asyncio
async def test_gbif_adapter_honore_le_mode_offline() -> None:
    client = FakeGBIFClient()
    adapter = GBIFAdapter(client)

    report = await adapter.health(AdapterContext(trace_id="gbif-offline", offline=True))

    assert report.status is DatasetHealthStatus.unknown
    assert report.error_code == "OFFLINE_MODE"
    assert client.match_calls == []


@pytest.mark.asyncio
async def test_gbif_adapter_delegue_les_operations_taxonomiques() -> None:
    client = FakeGBIFClient()
    adapter = GBIFAdapter(client)
    context = AdapterContext(trace_id="gbif-query")

    match = await adapter.query(
        AdapterQueryRequest(parameters={"operation": "species_match", "name": "Quercus robur"}),
        context,
    )
    vernacular = await adapter.query(
        AdapterQueryRequest(
            parameters={"operation": "vernacular_name", "taxon_key": 123, "language": "fra"}
        ),
        context,
    )

    assert match.items[0]["usageKey"] == 123
    assert vernacular.items[0]["name"] == "Chêne pédonculé"
    assert client.match_calls == ["Quercus robur"]
    assert client.vernacular_calls == [(123, "fra")]
    assert adapter.normalize(match)[0]["scientificName"] == "Quercus robur"


@pytest.mark.asyncio
async def test_gbif_adapter_health_convertit_une_panne_en_statut_stable() -> None:
    adapter = GBIFAdapter(FakeGBIFClient(fail=True))

    report = await adapter.health(AdapterContext(trace_id="gbif-health"))

    assert report.status is DatasetHealthStatus.unavailable
    assert report.error_code == "GBIF_HEALTH_CHECK_FAILED"
    assert report.latency_ms is not None


@pytest.mark.asyncio
async def test_gbif_adapter_refuse_les_requetes_incompletes() -> None:
    adapter = GBIFAdapter(FakeGBIFClient())
    context = AdapterContext(trace_id="gbif-invalid")

    with pytest.raises(ValueError, match="species_match"):
        await adapter.query(AdapterQueryRequest(parameters={"operation": "species_match"}), context)
    with pytest.raises(ValueError, match="inconnue"):
        await adapter.query(AdapterQueryRequest(parameters={"operation": "unknown"}), context)
    with pytest.raises(ValueError, match="taxon_key"):
        await adapter.query(
            AdapterQueryRequest(parameters={"operation": "vernacular_name", "taxon_key": True}),
            context,
        )


def test_gbif_descriptor_est_non_reseau_et_explicitement_allowliste() -> None:
    descriptor = GBIFAdapter(FakeGBIFClient()).descriptor

    assert descriptor.key == "gbif"
    assert descriptor.allowlisted_hosts == frozenset({"api.gbif.org"})
    assert descriptor.endpoint == "https://api.gbif.org/v1"
