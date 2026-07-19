"""Tests unitaires — schémas RFC-0016 (schéma forestier spécialisé, tranches 1-2/10).

Vérifie la règle non négociable du §3.1 : une classe de fertilité (ou un
modèle de fertilité, ou un profil autécologique) ne peut pas être
construit sans ses champs obligatoires — Pydantic doit refuser la
construction, pas produire un objet incomplet silencieusement. Vérifie
aussi (tranche 2) qu'une StationObservation sans StationType déterminé
doit obligatoirement porter une incertitude explicite (§4.3).
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
