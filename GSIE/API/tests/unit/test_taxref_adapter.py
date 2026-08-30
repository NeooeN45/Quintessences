"""Tests hors réseau de l'adapter TAXREF via miroir GBIF."""

import pytest

from gsie_api.data.adapters import AdapterContext, AdapterQueryRequest
from gsie_api.data.taxref_adapter import TaxrefAdapter
from gsie_api.engines.botanical.taxref_client import TaxrefClientError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

_RESULT = {
    "taxonID": "521658",
    "canonicalName": "Quercus petraea",
    "scientificName": "Quercus petraea (Matt.) Liebl., 1784",
    "species": "Quercus petraea",
    "family": "Fagaceae",
    "taxonomicStatus": "ACCEPTED",
}


class FakeTaxrefClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[str] = []

    async def search(self, nom_scientifique: str) -> dict[str, object] | None:
        if self.fail:
            raise TaxrefClientError("erreur TAXREF simulée")
        self.calls.append(nom_scientifique)
        return dict(_RESULT)


@pytest.mark.asyncio
async def test_taxref_adapter_interroge_le_miroir_et_normalise_la_provenance() -> None:
    client = FakeTaxrefClient()
    adapter = TaxrefAdapter(client)

    result = await adapter.query(
        AdapterQueryRequest(
            parameters={"operation": "search", "nom_scientifique": " Quercus petraea "}
        ),
        AdapterContext(trace_id="taxref-query"),
    )

    assert result.items[0]["taxonID"] == "521658"
    assert client.calls == ["Quercus petraea"]
    assert adapter.normalize(result)[0]["source_registry_id"] == "taxref-via-gbif"


@pytest.mark.asyncio
async def test_taxref_adapter_honore_le_mode_offline_et_une_panne() -> None:
    client = FakeTaxrefClient()
    adapter = TaxrefAdapter(client)
    offline = await adapter.health(AdapterContext(trace_id="taxref-offline", offline=True))

    assert offline.status is DatasetHealthStatus.unknown
    assert client.calls == []

    failed = await TaxrefAdapter(FakeTaxrefClient(fail=True)).health(
        AdapterContext(trace_id="taxref-health")
    )
    assert failed.status is DatasetHealthStatus.unavailable
    assert failed.error_code == "TAXREF_HEALTH_CHECK_FAILED"


@pytest.mark.asyncio
async def test_taxref_adapter_refuse_une_operation_ambiguë() -> None:
    with pytest.raises(ValueError, match="inconnue"):
        await TaxrefAdapter(FakeTaxrefClient()).query(
            AdapterQueryRequest(parameters={"operation": "occurrence"}),
            AdapterContext(trace_id="taxref-invalid"),
        )


def test_taxref_descriptor_pointe_vers_species_search_gbif() -> None:
    descriptor = TaxrefAdapter(FakeTaxrefClient()).descriptor

    assert descriptor.key == "taxref"
    assert descriptor.endpoint == "https://api.gbif.org/v1/species/search"
    assert descriptor.allowlisted_hosts == frozenset({"api.gbif.org"})
