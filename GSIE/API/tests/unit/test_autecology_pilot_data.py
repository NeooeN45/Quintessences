"""Tests unitaires — pilote réel d'ingestion AutecologyProfile (Quercus, RFC-0016 Phase C amorcée).

Vérifie que le curateur (`_CURATED_MAPPING`) construit bien 6 profils
réels et traçables à partir des faits vérifiés du 3e pilote RFC-0014
§3.6, et que toute ambiguïté de correspondance (`_fact_matching`) est
détectée plutôt que résolue silencieusement.
"""

from __future__ import annotations

import pytest

from gsie_api.seeds.autecology_pilot_data import (
    GBIF_TAXON_KEY_QUERCUS_PETRAEA,
    GBIF_TAXON_KEY_QUERCUS_ROBUR,
    _fact_matching,
    _load_facts,
    build_autecology_pilot_profiles,
)


def test_build_autecology_pilot_profiles_produces_six_profiles() -> None:
    profiles = build_autecology_pilot_profiles()
    assert len(profiles) == 6


def test_pilot_profiles_cover_both_species() -> None:
    profiles = build_autecology_pilot_profiles()
    keys = {p.species_gbif_taxon_key for p in profiles}
    assert keys == {GBIF_TAXON_KEY_QUERCUS_PETRAEA, GBIF_TAXON_KEY_QUERCUS_ROBUR}


def test_pilot_profiles_cover_three_variables() -> None:
    profiles = build_autecology_pilot_profiles()
    variables = {p.variable for p in profiles}
    assert variables == {
        "tolerance_engorgement_racinaire",
        "tolerance_secheresse",
        "preference_edaphique",
    }


def test_every_pilot_profile_traces_to_a_verified_citation() -> None:
    """Chaque profil doit citer la référence exacte du pilote — jamais

    une valeur affichée sans la preuve qui la classe (RFC-0016 §3.4).
    """
    profiles = build_autecology_pilot_profiles()
    for profile in profiles:
        assert "hal-02653679" in profile.method
        assert profile.value_text is not None
        assert profile.evidence_level == "B"


def test_fact_matching_raises_on_zero_matches() -> None:
    facts = _load_facts()
    with pytest.raises(ValueError, match="trouvé 0"):
        _fact_matching(facts, "phrase qui n'existe dans aucun fait")


def test_fact_matching_raises_on_ambiguous_match() -> None:
    facts = _load_facts()
    with pytest.raises(ValueError, match="trouvé"):
        _fact_matching(facts, "Quercus")  # présent dans presque tous les faits
