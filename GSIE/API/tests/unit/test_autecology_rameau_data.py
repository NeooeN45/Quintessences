"""Tests — extension autécologie Rameau (2008).

Vérifie que les profils Rameau sont conformes au schéma
`AutecologyProfileCreate`, sourcés, et que le corpus combiné
(Parelle + Rameau) est cohérent.
"""

from __future__ import annotations

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceType
from gsie_api.seeds.autecology_pilot_data import (
    GBIF_TAXON_KEY_QUERCUS_PETRAEA,
    GBIF_TAXON_KEY_QUERCUS_ROBUR,
    build_autecology_pilot_profiles,
)
from gsie_api.seeds.autecology_rameau_data import (
    GBIF_TAXON_KEY_ABIES_ALBA,
    GBIF_TAXON_KEY_FAGUS_SYLVATICA,
    GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
    GBIF_TAXON_KEY_QUERCUS_ILEX,
    all_autecology_profiles,
    build_autecology_rameau_profiles,
)


def should_build_20_rameau_profiles_for_4_species() -> None:
    """Rameau produit 20 profils (4 essences × 5 variables)."""
    profiles = build_autecology_rameau_profiles()
    assert len(profiles) == 20
    species_keys = {p.species_gbif_taxon_key for p in profiles}
    assert species_keys == {
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        GBIF_TAXON_KEY_ABIES_ALBA,
    }


def should_have_evidence_level_c_for_rameau() -> None:
    """Rameau est un référentiel de synthèse — niveau C, pas A ou B."""
    profiles = build_autecology_rameau_profiles()
    for p in profiles:
        assert p.evidence_level == EvidenceLevel.C


def should_have_rameau_source_on_all_profiles() -> None:
    """Tous les profils Rameau citent la Flore forestière française."""
    profiles = build_autecology_rameau_profiles()
    for p in profiles:
        assert p.source.type_source == SourceType.referentiel_officiel
        assert "Rameau" in p.source.auteur
        assert "2008" in p.source.date_publication
        assert "IDF" in p.source.reference


def should_have_textual_values_not_numeric() -> None:
    """Aucune valeur numérique inventée — valeurs textuelles uniquement (ADR-009)."""
    profiles = build_autecology_rameau_profiles()
    for p in profiles:
        assert p.value_text is not None
        assert len(p.value_text) > 10
        assert p.value_numeric is None


def should_cover_5_variables_per_species() -> None:
    """Chaque essence a ses 5 variables autécologiques."""
    profiles = build_autecology_rameau_profiles()
    expected_vars = {
        "preference_edaphique",
        "tolerance_secheresse",
        "exigence_lumiere",
        "altitude_preferee",
        "tolerance_gel",
    }
    for species_key in {
        GBIF_TAXON_KEY_FAGUS_SYLVATICA,
        GBIF_TAXON_KEY_PINUS_SYLVESTRIS,
        GBIF_TAXON_KEY_QUERCUS_ILEX,
        GBIF_TAXON_KEY_ABIES_ALBA,
    }:
        vars_for_species = {p.variable for p in profiles if p.species_gbif_taxon_key == species_key}
        assert (
            vars_for_species == expected_vars
        ), f"Variables manquantes pour {species_key}: {expected_vars - vars_for_species}"


def should_combine_parelle_and_rameau_in_corpus() -> None:
    """Le corpus combiné = 6 Parelle + 20 Rameau = 26 profils."""
    parelle = build_autecology_pilot_profiles()
    rameau = build_autecology_rameau_profiles()
    combined = all_autecology_profiles()
    assert len(combined) == len(parelle) + len(rameau)
    assert len(combined) == 26


def should_have_distinct_sources_in_combined_corpus() -> None:
    """Parelle et Rameau coexistent — deux sources distinctes pour Quercus."""
    combined = all_autecology_profiles()
    parelle_profiles = [p for p in combined if "Parelle" in p.source.auteur]
    rameau_profiles = [p for p in combined if "Rameau" in p.source.auteur]
    assert len(parelle_profiles) == 6
    assert len(rameau_profiles) == 20
    # Quercus robur et petraea ont des profils des deux sources
    quercus_parelle = {p.species_gbif_taxon_key for p in parelle_profiles}
    assert GBIF_TAXON_KEY_QUERCUS_ROBUR in quercus_parelle
    assert GBIF_TAXON_KEY_QUERCUS_PETRAEA in quercus_parelle


def should_have_method_tracing_rameau_synthesis() -> None:
    """Le champ method trace la synthèse Rameau (pas une heuristique)."""
    profiles = build_autecology_rameau_profiles()
    for p in profiles:
        assert "Rameau" in p.method
        assert "Flore forestière" in p.method
        assert "IDF" in p.method
