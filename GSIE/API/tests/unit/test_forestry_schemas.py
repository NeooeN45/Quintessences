"""Tests unitaires — schémas RFC-0016 (schéma forestier spécialisé, tranches 1-5/10).

Vérifie la règle non négociable du §3.1 : une classe de fertilité (ou un
modèle de fertilité, ou un profil autécologique) ne peut pas être
construit sans ses champs obligatoires — Pydantic doit refuser la
construction, pas produire un objet incomplet silencieusement. Vérifie
aussi (tranche 2) qu'une StationObservation sans StationType déterminé
doit obligatoirement porter une incertitude explicite (§4.3), (tranche 3)
qu'une SilviculturalRule passée à accepted sans validateur humain est
refusée (§3.2), (tranche 4) qu'un ProvenanceMaterial sans ses champs de
traçabilité MFR (région de provenance, catégorie, admissibilité, version
de l'arrêté) est refusé, et (tranche 5) qu'un HealthRisk avec un agent
causal confirmé mais sans méthode de confirmation est refusé.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from gsie_api.engines.botanical.schemas import AutecologyProfileCreate
from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.forest_dynamics.schemas import (
    FertilityClassCreate,
    HealthRiskCreate,
    ProvenanceMaterialCreate,
    SilviculturalRuleCreate,
    SilviculturalRuleRecord,
    SilviculturalSystemCreate,
    SiteIndexModelCreate,
    StationObservationCreate,
    StationTypeCreate,
)


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="ONF",
        reference="Mémento pin d'Alep, 2019",
    )


# --- SiteIndexModelCreate ---


def test_site_index_model_requires_all_non_negotiable_fields() -> None:
    model = SiteIndexModelCreate(
        species_gbif_taxon_key=5285725,
        name="Table de production pin d'Alep",
        method="table_de_production",
        reference_age_years=50,
        age_convention="âge réel",
        calibration_region="Provence calcaire",
        source=_source(),
    )
    assert model.reference_age_years == 50
    assert model.calibration_region == "Provence calcaire"


def test_site_index_model_rejects_incoherent_age_bounds() -> None:
    with pytest.raises(ValidationError, match="valid_age_min_years"):
        SiteIndexModelCreate(
            species_gbif_taxon_key=5285725,
            name="Table de production pin d'Alep",
            method="table_de_production",
            reference_age_years=50,
            age_convention="âge réel",
            calibration_region="Provence calcaire",
            valid_age_min_years=80,
            valid_age_max_years=20,
            source=_source(),
        )


@pytest.mark.parametrize(
    "missing_field",
    [
        "species_gbif_taxon_key",
        "reference_age_years",
        "age_convention",
        "calibration_region",
        "source",
    ],
)
def test_site_index_model_missing_required_field_raises(missing_field: str) -> None:
    payload = {
        "species_gbif_taxon_key": 5285725,
        "name": "Table de production pin d'Alep",
        "method": "table_de_production",
        "reference_age_years": 50,
        "age_convention": "âge réel",
        "calibration_region": "Provence calcaire",
        "source": _source(),
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        SiteIndexModelCreate(**payload)


# --- FertilityClassCreate ---


def test_fertility_class_requires_all_non_negotiable_fields() -> None:
    fertility_class = FertilityClassCreate(
        species_gbif_taxon_key=5285725,
        site_index_model_id=uuid4(),
        class_label="Classe 1",
        reference_age_years=50,
        calibration_region="Provence calcaire",
        source=_source(),
    )
    assert fertility_class.class_label == "Classe 1"


@pytest.mark.parametrize(
    "missing_field",
    [
        "species_gbif_taxon_key",
        "site_index_model_id",
        "class_label",
        "reference_age_years",
        "calibration_region",
        "source",
    ],
)
def test_fertility_class_missing_required_field_raises(missing_field: str) -> None:
    """Reproduit littéralement la règle RFC-0016 §3.1 : une classe de fertilité

    sans species_id/model_id/âge de référence/région de calibration/source
    est un bug de sécurité scientifique — ici vérifié champ par champ.
    """
    payload = {
        "species_gbif_taxon_key": 5285725,
        "site_index_model_id": uuid4(),
        "class_label": "Classe 1",
        "reference_age_years": 50,
        "calibration_region": "Provence calcaire",
        "source": _source(),
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        FertilityClassCreate(**payload)


def test_fertility_class_rejects_incoherent_bounds() -> None:
    with pytest.raises(ValidationError, match="lower_bound_m"):
        FertilityClassCreate(
            species_gbif_taxon_key=5285725,
            site_index_model_id=uuid4(),
            class_label="Classe 1",
            reference_age_years=50,
            calibration_region="Provence calcaire",
            lower_bound_m=20.0,
            upper_bound_m=10.0,
            source=_source(),
        )


def test_fertility_class_extra_field_rejected() -> None:
    """`extra="forbid"` : un champ non prévu (ex. un entier nu déguisé) est rejeté."""
    with pytest.raises(ValidationError):
        FertilityClassCreate(
            species_gbif_taxon_key=5285725,
            site_index_model_id=uuid4(),
            class_label="Classe 1",
            reference_age_years=50,
            calibration_region="Provence calcaire",
            source=_source(),
            fertility_class_bare_integer=1,
        )


# --- AutecologyProfileCreate ---


def test_autecology_profile_requires_a_value() -> None:
    with pytest.raises(ValidationError, match="value_numeric ou value_text"):
        AutecologyProfileCreate(
            species_gbif_taxon_key=5285725,
            variable="ph_optimal",
            evidence_level="B",
            source=_source(),
        )


def test_autecology_profile_accepts_numeric_value() -> None:
    profile = AutecologyProfileCreate(
        species_gbif_taxon_key=5285725,
        variable="ph_optimal",
        value_numeric=6.5,
        unit="pH",
        evidence_level="B",
        source=_source(),
    )
    assert profile.value_numeric == 6.5


def test_autecology_profile_accepts_text_value_without_numeric() -> None:
    profile = AutecologyProfileCreate(
        species_gbif_taxon_key=5285725,
        variable="tolerance_secheresse",
        value_text="Élevée",
        evidence_level="B",
        source=_source(),
    )
    assert profile.value_text == "Élevée"


# --- StationTypeCreate / StationObservationCreate (tranche 2/10) ---


def test_station_type_requires_guide_and_validity_zone() -> None:
    station_type = StationTypeCreate(
        guide="Guide des stations forestières Aquitaine",
        guide_version="2019",
        validity_zone_description="Landes de Gascogne, plateau sableux",
        ser_greco_code="B22",
        source=_source(),
    )
    assert station_type.guide_version == "2019"


@pytest.mark.parametrize(
    "missing_field", ["guide", "guide_version", "validity_zone_description", "source"]
)
def test_station_type_missing_required_field_raises(missing_field: str) -> None:
    payload = {
        "guide": "Guide des stations forestières Aquitaine",
        "guide_version": "2019",
        "validity_zone_description": "Landes de Gascogne, plateau sableux",
        "source": _source(),
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        StationTypeCreate(**payload)


def test_station_observation_with_determined_type_does_not_require_uncertainty() -> None:
    observation = StationObservationCreate(
        plot_reference="parcelle-12-A",
        station_type_id=uuid4(),
        key_path_followed="Q1=oui, Q2=drainé -> type B22-a",
        observed_at=datetime(2026, 7, 19, tzinfo=UTC),
        source=_source(),
    )
    assert observation.station_type_id is not None


def test_station_observation_without_determined_type_requires_uncertainty() -> None:
    """Reproduit littéralement RFC-0016 §4.3 : pas de rattachement arbitraire

    quand la clé du guide ne résout aucun StationType avec certitude —
    l'incertitude doit être explicite, pas silencieusement absente.
    """
    with pytest.raises(ValidationError, match="determination_uncertainty"):
        StationObservationCreate(
            plot_reference="parcelle-12-A",
            station_type_id=None,
            observed_at=datetime(2026, 7, 19, tzinfo=UTC),
            source=_source(),
        )


def test_station_observation_without_determined_type_accepted_with_uncertainty() -> None:
    observation = StationObservationCreate(
        plot_reference="parcelle-12-A",
        station_type_id=None,
        determination_uncertainty="Deux embranchements possibles selon l'humidité au relevé",
        observed_at=datetime(2026, 7, 19, tzinfo=UTC),
        source=_source(),
    )
    assert observation.station_type_id is None
    assert observation.determination_uncertainty is not None


# --- SilviculturalSystemCreate / SilviculturalRuleCreate (tranche 3/10) ---


def test_silvicultural_system_requires_name_and_category() -> None:
    system = SilviculturalSystemCreate(
        name="Futaie régulière de pin d'Alep",
        category="futaie_reguliere",
        source=_source(),
    )
    assert system.category == "futaie_reguliere"


@pytest.mark.parametrize("missing_field", ["name", "category", "source"])
def test_silvicultural_system_missing_required_field_raises(missing_field: str) -> None:
    payload = {
        "name": "Futaie régulière de pin d'Alep",
        "category": "futaie_reguliere",
        "source": _source(),
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        SilviculturalSystemCreate(**payload)


def test_silvicultural_rule_requires_all_non_negotiable_fields() -> None:
    rule = SilviculturalRuleCreate(
        required_context="Peuplement régulier, densité > 800 tiges/ha",
        trigger="Surface terrière > 30 m²/ha",
        action="Éclaircie par le bas",
        intensity="Prélever 25 % de la surface terrière",
        evidence_level="B",
        source=_source(),
    )
    assert rule.action == "Éclaircie par le bas"


@pytest.mark.parametrize(
    "missing_field",
    ["required_context", "trigger", "action", "intensity", "evidence_level", "source"],
)
def test_silvicultural_rule_missing_required_field_raises(missing_field: str) -> None:
    payload = {
        "required_context": "Peuplement régulier, densité > 800 tiges/ha",
        "trigger": "Surface terrière > 30 m²/ha",
        "action": "Éclaircie par le bas",
        "intensity": "Prélever 25 % de la surface terrière",
        "evidence_level": "B",
        "source": _source(),
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        SilviculturalRuleCreate(**payload)


def test_silvicultural_rule_record_accepted_requires_human_validator() -> None:
    """Reproduit littéralement RFC-0016 §3.2 : jamais d'auto-validation par

    le pipeline d'extraction — le passage à accepted exige un validateur
    humain explicite (curateur de données + forestier compétent).
    """
    with pytest.raises(ValidationError, match="human_validator"):
        SilviculturalRuleRecord(
            id=uuid4(),
            required_context="Peuplement régulier, densité > 800 tiges/ha",
            trigger="Surface terrière > 30 m²/ha",
            action="Éclaircie par le bas",
            intensity="Prélever 25 % de la surface terrière",
            evidence_level="B",
            source=_source(),
            status="accepted",
        )


def test_silvicultural_rule_record_accepted_with_human_validator_passes() -> None:
    rule = SilviculturalRuleRecord(
        id=uuid4(),
        required_context="Peuplement régulier, densité > 800 tiges/ha",
        trigger="Surface terrière > 30 m²/ha",
        action="Éclaircie par le bas",
        intensity="Prélever 25 % de la surface terrière",
        evidence_level="B",
        source=_source(),
        status="accepted",
        human_validator="J. Dupont, forestier référent CNPF",
    )
    assert rule.status == "accepted"


def test_silvicultural_rule_record_draft_does_not_require_human_validator() -> None:
    rule = SilviculturalRuleRecord(
        id=uuid4(),
        required_context="Peuplement régulier, densité > 800 tiges/ha",
        trigger="Surface terrière > 30 m²/ha",
        action="Éclaircie par le bas",
        intensity="Prélever 25 % de la surface terrière",
        evidence_level="B",
        source=_source(),
        status="draft",
    )
    assert rule.human_validator is None


# --- ProvenanceMaterialCreate (tranche 4/10) ---


def test_provenance_material_requires_all_non_negotiable_fields() -> None:
    material = ProvenanceMaterialCreate(
        species_gbif_taxon_key=5285725,
        provenance_region="Massif central",
        base_material="Verger à graines qualifié VG-034",
        base_material_category="qualifie",
        aid_eligible=True,
        decree_version="Arrêté MFR du 6 mars 2026",
        source=_source(),
    )
    assert material.aid_eligible is True


@pytest.mark.parametrize(
    "missing_field",
    [
        "species_gbif_taxon_key",
        "provenance_region",
        "base_material",
        "base_material_category",
        "aid_eligible",
        "decree_version",
        "source",
    ],
)
def test_provenance_material_missing_required_field_raises(missing_field: str) -> None:
    """Reproduit littéralement RFC-0016 §3.1 : un matériel « admissible »

    sans la version de l'arrêté qui le rend admissible est le même bug
    de sécurité scientifique qu'une classe de fertilité sans région de
    calibration — vérifié champ par champ.
    """
    payload = {
        "species_gbif_taxon_key": 5285725,
        "provenance_region": "Massif central",
        "base_material": "Verger à graines qualifié VG-034",
        "base_material_category": "qualifie",
        "aid_eligible": True,
        "decree_version": "Arrêté MFR du 6 mars 2026",
        "source": _source(),
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        ProvenanceMaterialCreate(**payload)


def test_provenance_material_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        ProvenanceMaterialCreate(
            species_gbif_taxon_key=5285725,
            provenance_region="Massif central",
            base_material="Verger à graines qualifié VG-034",
            base_material_category="qualifie",
            aid_eligible=True,
            decree_version="Arrêté MFR du 6 mars 2026",
            source=_source(),
            provenance_bare_integer=1,
        )


# --- HealthRiskCreate (tranche 5/10) ---


def test_health_risk_requires_symptom_observed() -> None:
    risk = HealthRiskCreate(
        subject_id=uuid4(),
        symptom_observed="Défoliation de la couronne, jaunissement des aiguilles",
        observed_at=datetime(2026, 7, 19, tzinfo=UTC),
        source=_source(),
    )
    assert risk.symptom_observed.startswith("Défoliation")


def test_health_risk_missing_symptom_observed_raises() -> None:
    with pytest.raises(ValidationError):
        HealthRiskCreate(
            subject_id=uuid4(),
            observed_at=datetime(2026, 7, 19, tzinfo=UTC),
            source=_source(),
        )


def test_health_risk_accepts_suspected_agent_without_confirmation() -> None:
    risk = HealthRiskCreate(
        subject_id=uuid4(),
        symptom_observed="Chancre au collet",
        suspected_causal_agent="Phytophthora sp. (suspecté)",
        observed_at=datetime(2026, 7, 19, tzinfo=UTC),
        source=_source(),
    )
    assert risk.confirmed_causal_agent is None


def test_health_risk_confirmed_agent_without_method_raises() -> None:
    """Reproduit littéralement RFC-0016 §3.1 : un agent causal « confirmé »

    sans méthode de confirmation citée serait une invention silencieuse
    (ADR-007), pas une simplification acceptable.
    """
    with pytest.raises(ValidationError, match="confirmation_method"):
        HealthRiskCreate(
            subject_id=uuid4(),
            symptom_observed="Chancre au collet",
            confirmed_causal_agent="Phytophthora cinnamomi",
            observed_at=datetime(2026, 7, 19, tzinfo=UTC),
            source=_source(),
        )


def test_health_risk_confirmed_agent_with_method_passes() -> None:
    risk = HealthRiskCreate(
        subject_id=uuid4(),
        symptom_observed="Chancre au collet",
        confirmed_causal_agent="Phytophthora cinnamomi",
        confirmation_method="Analyse PCR en laboratoire agréé, 2026-07-15",
        severity="high",
        observed_at=datetime(2026, 7, 19, tzinfo=UTC),
        source=_source(),
    )
    assert risk.confirmed_causal_agent == "Phytophthora cinnamomi"
