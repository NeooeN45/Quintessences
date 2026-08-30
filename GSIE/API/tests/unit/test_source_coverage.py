"""Tests de complétude et de sécurité de la matrice des sources."""

from __future__ import annotations

from gsie_api.data.adapters import AdapterCapability
from gsie_api.data.bootstrap import build_adapter_registry
from gsie_api.governance.source_coverage import (
    SOURCE_COVERAGE,
    SourceOperationalStatus,
    audit_source_coverage,
)
from gsie_api.governance.source_registry import SCIENTIFIC_SOURCES


def test_la_matrice_couvre_exactement_le_registre_scientifique() -> None:
    audit = audit_source_coverage(adapter_registry=build_adapter_registry())

    assert {item.source_id for item in audit.entries} == set(SCIENTIFIC_SOURCES)
    assert len(SOURCE_COVERAGE) == len(SCIENTIFIC_SOURCES)


def test_le_controle_signale_l_adapter_soilgrids_interdit_et_non_lie() -> None:
    audit = audit_source_coverage(adapter_registry=build_adapter_registry())

    assert not audit.valid
    assert "ADAPTER_WITHOUT_SOURCE_BINDING:soilgrids" in audit.errors
    assert "soilgrids-rest-beta" in {
        item.source_id for item in audit.entries if item.status is SourceOperationalStatus.BLOCKED
    }


def test_les_trois_requetes_actuelles_exigent_query_et_mode_metadata() -> None:
    audit = audit_source_coverage(adapter_registry=build_adapter_registry())

    query_entries = {
        item.source_id: item
        for item in audit.entries
        if item.status is SourceOperationalStatus.ADAPTER_QUERY
    }
    assert set(query_entries) == {
        "gbif-species-api",
        "ign-apicarto-cadastre",
        "meteofrance-meteo-forets",
    }
    assert all(item.adapter_key is not None for item in query_entries.values())
    assert all(
        item.required_capability is AdapterCapability.QUERY for item in query_entries.values()
    )


def test_une_nouvelle_source_sans_ligne_de_couverture_est_refusee() -> None:
    source_id, entry = next(iter(SCIENTIFIC_SOURCES.items()))
    entries = dict(SCIENTIFIC_SOURCES)
    entries["source-nouvelle-de-test"] = entry.model_copy(
        update={"identifiant": "source-nouvelle-de-test"}
    )

    audit = audit_source_coverage(source_entries=entries)

    assert "SOURCE_COVERAGE_MISSING:source-nouvelle-de-test" in audit.errors
    assert source_id in {item.source_id for item in audit.entries}
