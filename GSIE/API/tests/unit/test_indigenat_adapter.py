"""Tests hors réseau de l'adapter Indigénat Bellifa."""

import pytest

from gsie_api.data.adapters import AdapterContext, AdapterQueryRequest
from gsie_api.data.indigenat_adapter import IndigenatBellifaAdapter
from gsie_api.engines.botanical.indigenat_loader import IndigenatLoaderError
from gsie_api.infrastructure.models.enums import DatasetHealthStatus

_ROW = {
    "CD_NOM_TaxRefv18.0": "521658",
    "Nom_scientifique": "Quercus petraea (Matt.) Liebl., 1784",
    "Nom_vernaculaire": "Chêne sessile",
    "Famille": "Fagaceae",
    "Indigenat FR": "Indigène",
    "A11": "1",
}


class FakeIndigenatLoader:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[int | None, str | None]] = []

    def find(self, cd_nom: int | None, nom_scientifique: str | None) -> dict[str, str] | None:
        if self.fail:
            raise IndigenatLoaderError("dataset Bellifa simulé absent")
        self.calls.append((cd_nom, nom_scientifique))
        return dict(_ROW)


@pytest.mark.asyncio
async def test_indigenat_adapter_retourne_la_ligne_reelle_et_le_code_ser() -> None:
    loader = FakeIndigenatLoader()
    adapter = IndigenatBellifaAdapter(loader)

    result = await adapter.query(
        AdapterQueryRequest(
            parameters={
                "operation": "find",
                "cd_nom": 521658,
                "code_ser": "A11",
            }
        ),
        AdapterContext(trace_id="indigenat-query"),
    )

    assert result.items[0]["CD_NOM_TaxRefv18.0"] == "521658"
    assert result.items[0]["code_ser"] == "A11"
    assert result.items[0]["source_registry_id"] == "indigenat-bellifa-2026"
    assert loader.calls == [(521658, None)]


@pytest.mark.asyncio
async def test_indigenat_adapter_ne_fabrique_pas_de_resultat_pour_une_ser_absente() -> None:
    loader = FakeIndigenatLoader()
    result = await IndigenatBellifaAdapter(loader).query(
        AdapterQueryRequest(
            parameters={"operation": "find", "nom_scientifique": "Quercus", "code_ser": "Z99"}
        ),
        AdapterContext(trace_id="indigenat-empty"),
    )

    assert result.items == ()


@pytest.mark.asyncio
async def test_indigenat_adapter_verifie_la_lecture_du_dataset_et_le_mode_offline() -> None:
    loader = FakeIndigenatLoader()
    adapter = IndigenatBellifaAdapter(loader)
    offline = await adapter.health(AdapterContext(trace_id="indigenat-offline", offline=True))

    assert offline.status is DatasetHealthStatus.unknown
    assert loader.calls == []

    healthy = await adapter.health(AdapterContext(trace_id="indigenat-health"))
    assert healthy.status is DatasetHealthStatus.healthy
    failed = await IndigenatBellifaAdapter(FakeIndigenatLoader(fail=True)).health(
        AdapterContext(trace_id="indigenat-failed")
    )
    assert failed.status is DatasetHealthStatus.unavailable
    assert failed.error_code == "INDIGENAT_HEALTH_CHECK_FAILED"


def test_indigenat_descriptor_est_local_sans_egress() -> None:
    descriptor = IndigenatBellifaAdapter(FakeIndigenatLoader()).descriptor

    assert descriptor.key == "indigenat-bellifa"
    assert descriptor.endpoint is None
    assert descriptor.allowlisted_hosts == frozenset()
