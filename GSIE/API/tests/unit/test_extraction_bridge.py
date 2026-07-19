"""Tests unitaires — pont extraction documentaire → AutecologyProfile.

RFC-0016 §5, Phase B, point 4.

Vérifie que le pont refuse tout fait qui n'est pas en statut
`quarantine` (un fait déjà rejeté par la vérification de citation ne
doit jamais devenir une AutecologyProfile), et qu'il ne dérive jamais
`variable`/valeur automatiquement — ce sont toujours des décisions du
curateur humain fournies explicitement.

Le test `test_real_pilot_facts_load_and_bridge` rejoue les faits réels
du troisième pilote RFC-0014 §3.6
(`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`)
pour garantir que le pont fonctionne sur des données réellement
extraites, pas seulement sur des fixtures synthétiques.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gsie_api.engines.botanical.extraction_bridge import (
    ExtractionBridgeError,
    QuarantinedFact,
    build_autecology_profile_from_quarantined_fact,
)
from gsie_api.engines.evidence.schemas import SourceReference, SourceType

_PILOT_FACTS_PATH = (
    Path(__file__).resolve().parents[4]
    / "GSIE"
    / "KNOWLEDGE"
    / "pilotes_extraction"
    / "parelle_2007_quercus_waterlogging_facts.json"
)


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Parelle J., Brendel O., Jolivet Y.",
        reference="Annals of Forest Science (2007), hal-02653679",
    )


def _quarantined_fact(**overrides: object) -> QuarantinedFact:
    payload: dict[str, object] = {
        "document_title": "Intra- and interspecific diversity in the response to waterlogging",
        "document_reference": "Parelle et al. (2007), Annals of Forest Science, hal-02653679",
        "page_number": 2,
        "fait": "Quercus petraea se trouve sur des sols acides profonds et bien drainés.",
        "citation_extrait": "Q. petraea is found on deep and well drained acidic soils",
        "confiance_llm": 1.0,
        "statut": "quarantine",
        "rejet_raison": None,
    }
    payload.update(overrides)
    return QuarantinedFact(**payload)


def test_bridge_builds_profile_with_curator_supplied_variable_and_value() -> None:
    profile = build_autecology_profile_from_quarantined_fact(
        _quarantined_fact(),
        species_gbif_taxon_key=2879059,
        variable="preference_sol_acide_drainant",
        evidence_level="A",
        source=_source(),
        value_text="Sols acides profonds et bien drainés",
    )
    assert profile.variable == "preference_sol_acide_drainant"
    assert profile.value_text == "Sols acides profonds et bien drainés"
    assert "hal-02653679" in profile.method
    assert "p. 2" in profile.method
    assert "Q. petraea is found on deep and well drained acidic soils" in profile.method


def test_bridge_rejects_fact_not_in_quarantine_status() -> None:
    """Un fait déjà `rejete` (citation introuvable) ne doit jamais devenir

    une AutecologyProfile, quelle que soit la décision du curateur.
    """
    with pytest.raises(ExtractionBridgeError, match="rejete"):
        build_autecology_profile_from_quarantined_fact(
            _quarantined_fact(statut="rejete", rejet_raison="citation introuvable"),
            species_gbif_taxon_key=2879059,
            variable="preference_sol_acide_drainant",
            evidence_level="A",
            source=_source(),
            value_text="Sols acides profonds et bien drainés",
        )


def test_bridge_still_requires_a_value_from_curator() -> None:
    """Le pont ne dérive jamais la valeur du texte du fait — sans

    value_numeric ni value_text fournis par le curateur, la construction
    de l'AutecologyProfileCreate sous-jacente échoue toujours (§3.1).
    """
    with pytest.raises(ValueError, match="value_numeric ou value_text"):
        build_autecology_profile_from_quarantined_fact(
            _quarantined_fact(),
            species_gbif_taxon_key=2879059,
            variable="preference_sol_acide_drainant",
            evidence_level="A",
            source=_source(),
        )


def test_real_pilot_facts_load_and_bridge() -> None:
    """Rejoue les faits réels du 3e pilote RFC-0014 §3.6 sur des chênes.

    Ne construit une AutecologyProfile que pour les faits en
    quarantine ET qui décrivent effectivement une variable autécologique
    (le pilote contient aussi des faits méthodologiques, ex. le
    protocole d'engorgement en pot, qui ne sont pas une observation
    autécologique du taxon — ce tri reste une décision du curateur, pas
    une heuristique de ce test).
    """
    raw_facts = json.loads(_PILOT_FACTS_PATH.read_text(encoding="utf-8"))
    facts = [QuarantinedFact(**entry) for entry in raw_facts]

    quarantine_facts = [f for f in facts if f.statut == "quarantine"]
    rejected_facts = [f for f in facts if f.statut == "rejete"]
    assert len(quarantine_facts) == 29
    assert len(rejected_facts) == 2

    # Un seul fait autécologique choisi manuellement pour vérifier le pont
    # bout en bout — pas un traitement en masse (justement parce que le
    # tri variable/valeur n'est pas automatisable, voir docstring module).
    drought_fact = next(
        f for f in quarantine_facts if "sécheresse" in f.fait and "petraea" in f.fait
    )
    profile = build_autecology_profile_from_quarantined_fact(
        drought_fact,
        species_gbif_taxon_key=2879059,
        variable="tolerance_secheresse_relative",
        evidence_level="B",
        source=_source(),
        value_text="Plus tolérant à la sécheresse que Quercus robur",
    )
    assert profile.value_text == "Plus tolérant à la sécheresse que Quercus robur"
    assert str(drought_fact.page_number) in profile.method
