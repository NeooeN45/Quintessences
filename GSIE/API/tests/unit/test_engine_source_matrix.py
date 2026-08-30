"""Tests du contrat moteur -> sources, sans réseau ni base de données."""

from dataclasses import replace

from gsie_api.governance.engine_source_matrix import (
    ENGINE_SOURCE_MATRIX,
    EngineSourceMode,
    audit_engine_source_matrix,
)


def test_la_matrice_declares_exactement_les_quatorze_moteurs_bench() -> None:
    audit = audit_engine_source_matrix()

    assert audit.valid, audit.errors
    assert len(audit.bindings) == 14
    assert audit.counts == {
        "ADAPTER_QUERY": 4,
        "FORGE_HANDOFF": 1,
        "INDIRECT_REGISTRY": 9,
    }


def test_les_sources_directes_sont_couvertes_par_le_registre_operationnel() -> None:
    audit = audit_engine_source_matrix()
    direct = {
        source_id
        for binding in audit.bindings
        if binding.mode is not EngineSourceMode.INDIRECT_REGISTRY
        for source_id in binding.source_ids
    }

    assert direct == {
        "ign-apicarto-cadastre",
        "meteofrance-meteo-forets",
        "soilgrids-wcs",
        "gbif-species-api",
        "taxref-via-gbif",
        "indigenat-bellifa-2026",
        "ifn-donnees-brutes",
    }


def test_un_moteur_ne_peut_pas_declarer_le_rest_soilgrids_bloque() -> None:
    modified = tuple(
        replace(
            binding,
            source_ids=("soilgrids-rest-beta",),
            mode=EngineSourceMode.ADAPTER_QUERY,
        )
        if binding.engine_id == "pedology"
        else binding
        for binding in ENGINE_SOURCE_MATRIX
    )

    audit = audit_engine_source_matrix(bindings=modified)

    assert "ENGINE_SOURCE_FORBIDDEN_SOURCE:pedology:soilgrids-rest-beta" in audit.errors
    assert not audit.valid


def test_une_dependance_inconnue_est_refusee() -> None:
    modified = tuple(
        replace(
            binding,
            source_ids=("source-inconnue",),
            mode=EngineSourceMode.ADAPTER_QUERY,
        )
        if binding.engine_id == "gis"
        else binding
        for binding in ENGINE_SOURCE_MATRIX
    )

    audit = audit_engine_source_matrix(bindings=modified)

    assert "ENGINE_SOURCE_UNKNOWN_SOURCE:gis:source-inconnue" in audit.errors


def test_les_candidats_recherche_ne_sont_pas_treates_comme_des_sources_actives() -> None:
    candidates = {
        candidate
        for binding in ENGINE_SOURCE_MATRIX
        for candidate in binding.candidate_sources
    }

    assert "BD Forêt v2" in candidates
    assert "SAFRAN" in candidates
    assert "BD Forêt v2" not in {
        source_id for binding in ENGINE_SOURCE_MATRIX for source_id in binding.source_ids
    }
