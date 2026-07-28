"""Tests — adaptateur AutecologyProfile → RegleInference.

Vérifie que l'adaptateur transforme correctement les profils autécologiques
(Parelle + Rameau) en règles d'inférence consommables par le Reasoning
Engine, avec source, niveau de preuve et confiance cohérents.
"""

from __future__ import annotations

import pytest

from gsie_api.engines.autecology_adapter import (
    AutecologyAdapterError,
    profile_to_rule,
    profiles_to_rules,
)
from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.seeds.autecology_pilot_data import (
    GBIF_TAXON_KEY_QUERCUS_ROBUR,
    build_autecology_pilot_profiles,
)
from gsie_api.seeds.autecology_rameau_data import (
    GBIF_TAXON_KEY_FAGUS_SYLVATICA,
    build_autecology_rameau_profiles,
)


def should_convert_rameau_profile_to_rule() -> None:
    """Un profil Rameau devient une règle avec condition sur l'essence."""
    profiles = build_autecology_rameau_profiles()
    fagus_edaphique = next(
        p
        for p in profiles
        if p.species_gbif_taxon_key == GBIF_TAXON_KEY_FAGUS_SYLVATICA
        and p.variable == "preference_edaphique"
    )
    rule = profile_to_rule(fagus_edaphique)
    assert "fagus_sylvatica" in rule.identifiant
    assert rule.condition == "peuplement_essence_cible == 'Fagus sylvatica'"
    assert "Fagus sylvatica" in rule.enonce_conclusion
    assert "sols" in rule.enonce_conclusion.lower()
    assert rule.evidence_level == EvidenceLevel.C
    assert rule.niveau_confiance == 0.60


def should_convert_parelle_profile_to_rule() -> None:
    """Un profil Parelle (grade B) devient une règle avec confiance 0.80."""
    profiles = build_autecology_pilot_profiles()
    quercus_waterlogging = next(
        p
        for p in profiles
        if p.species_gbif_taxon_key == GBIF_TAXON_KEY_QUERCUS_ROBUR
        and p.variable == "tolerance_engorgement_racinaire"
    )
    rule = profile_to_rule(quercus_waterlogging)
    assert "quercus_robur" in rule.identifiant
    assert rule.condition == "peuplement_essence_cible == 'Quercus robur'"
    assert rule.evidence_level == EvidenceLevel.B
    assert rule.niveau_confiance == 0.80


def should_preserve_source_in_rule() -> None:
    """La source du profil est reportée dans la règle (GSIE-CON-002)."""
    profiles = build_autecology_rameau_profiles()
    rule = profile_to_rule(profiles[0])
    assert rule.source is not None
    assert "Rameau" in rule.source.auteur


def should_raise_for_unknown_species() -> None:
    """Une espèce non résolue lève une erreur explicite."""
    from gsie_api.engines.botanical.schemas import AutecologyProfileCreate
    from gsie_api.engines.evidence.schemas import SourceReference, SourceType

    profile = AutecologyProfileCreate(
        species_gbif_taxon_key=999999999,  # espèce inconnue
        variable="preference_edaphique",
        value_text="test",
        evidence_level=EvidenceLevel.C,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="Test",
            date_publication="2026",
            reference="test",
        ),
    )
    with pytest.raises(AutecologyAdapterError, match="non résolue"):
        profile_to_rule(profile)


def should_sort_rules_by_identifiant_for_determinism() -> None:
    """Les règles sont triées par identifiant (déterminisme Reasoning)."""
    profiles = build_autecology_rameau_profiles()
    rules = profiles_to_rules(profiles)
    identifiers = [r.identifiant for r in rules]
    assert identifiers == sorted(identifiers)


def should_generate_one_rule_per_profile() -> None:
    """20 profils Rameau → 20 règles."""
    profiles = build_autecology_rameau_profiles()
    rules = profiles_to_rules(profiles)
    assert len(rules) == len(profiles) == 20


def should_have_distinct_identifiers_per_rule() -> None:
    """Chaque règle a un identifiant unique (espèce + variable)."""
    profiles = build_autecology_rameau_profiles()
    rules = profiles_to_rules(profiles)
    identifiers = [r.identifiant for r in rules]
    assert len(identifiers) == len(set(identifiers))


def should_map_grade_to_confidence_monotonically() -> None:
    """La confiance est monotone croissante avec le grade (A > B > C)."""
    profiles_parelle = build_autecology_pilot_profiles()  # grade B
    profiles_rameau = build_autecology_rameau_profiles()  # grade C
    rule_b = profile_to_rule(profiles_parelle[0])
    rule_c = profile_to_rule(profiles_rameau[0])
    assert rule_b.niveau_confiance > rule_c.niveau_confiance
    assert rule_b.evidence_level == EvidenceLevel.B
    assert rule_c.evidence_level == EvidenceLevel.C
