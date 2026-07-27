"""Tests — modèles de croissance calibrés IGN et backend de simulation.

Vérifie que le modèle calibré (CalibratedGrowthBackend) projette
correctement le volume et la circonférence des essences, avec sources
IGN et hypothèses explicites. Couvre aussi l'architecture strategy
(LinearGrowthBackend vs CalibratedGrowthBackend vs CapsisBackend).
"""

from __future__ import annotations

import pytest

from gsie_api.engines.growth_models import (
    GrowthModelError,
    available_species,
    get_growth_parameters,
    project_circumference,
    project_volume,
)
from gsie_api.engines.simulation_backend import (
    CalibratedGrowthBackend,
    CapsisBackend,
    LinearGrowthBackend,
    SimulationBackendError,
)
from gsie_api.engines.simulation.schemas import ConfidenceLevel


# --- Tests growth_models.py ---


def should_calibrate_6_species() -> None:
    """Le référentiel calibre les 6 essences du corpus autécologique."""
    species = available_species()
    assert len(species) == 6
    assert "Fagus sylvatica" in species
    assert "Quercus petraea" in species
    assert "Quercus robur" in species
    assert "Pinus sylvestris" in species
    assert "Quercus ilex" in species
    assert "Abies alba" in species


def should_return_growth_parameters_for_known_species() -> None:
    """Les paramètres de croissance sont retrievables par essence."""
    params = get_growth_parameters("Fagus sylvatica")
    assert params.species_name == "Fagus sylvatica"
    assert params.accroissement_moyen_annuel_volume > 0
    assert params.accroissement_moyen_annuel_circonference > 0
    assert params.production_maximale_volume > 0
    assert "IGN" in params.source.auteur


def should_raise_for_unknown_species() -> None:
    """Une essence non calibrée lève une erreur explicite."""
    with pytest.raises(GrowthModelError, match="non calibrée"):
        get_growth_parameters("Unknown species")


def should_project_volume_linearly_with_ama() -> None:
    """La projection de volume est linéaire : initial + AMA × horizon."""
    result = project_volume("Fagus sylvatica", initial_volume=100.0, horizon_years=10)
    # AMA Fagus = 7.0 m³/ha/an, sur 10 ans = 70 m³/ha
    assert result["final_volume"] == pytest.approx(170.0)
    assert result["increment"] == pytest.approx(70.0)
    assert result["annual_increment"] == pytest.approx(7.0)
    assert result["capped"] is False
    assert "IGN" in result["source"]


def should_cap_volume_at_production_maximale() -> None:
    """La projection est plafonnée par la production maximale à maturité."""
    # Fagus : production max = 500 m³/ha, AMA = 7.0
    # Initial = 480, horizon = 10 → 480 + 70 = 550 > 500 → capped
    result = project_volume("Fagus sylvatica", initial_volume=480.0, horizon_years=10)
    assert result["final_volume"] == pytest.approx(500.0)
    assert result["capped"] is True
    assert result["increment"] == pytest.approx(20.0)  # 500 - 480


def should_apply_density_factor_to_increment() -> None:
    """Le facteur de densité module l'accroissement."""
    full = project_volume("Fagus sylvatica", 100.0, 10, density_factor=1.0)
    half = project_volume("Fagus sylvatica", 100.0, 10, density_factor=0.5)
    assert full["annual_increment"] == pytest.approx(7.0)
    assert half["annual_increment"] == pytest.approx(3.5)
    assert half["final_volume"] < full["final_volume"]


def should_reject_negative_initial_volume() -> None:
    """Un volume initial négatif est rejeté."""
    with pytest.raises(GrowthModelError, match="négatif"):
        project_volume("Fagus sylvatica", -10.0, 10)


def should_reject_invalid_density_factor() -> None:
    """Un facteur de densité hors [0,1] est rejeté."""
    with pytest.raises(GrowthModelError, match="hors"):
        project_volume("Fagus sylvatica", 100.0, 10, density_factor=1.5)


def should_project_circumference_linearly() -> None:
    """La projection de circonférence est linéaire : initial + AMA × horizon."""
    result = project_circumference("Pinus sylvestris", initial_circumference=50.0, horizon_years=10)
    # AMA circonférence Pinus = 2.5 cm/an, sur 10 ans = 25 cm
    assert result["final_circumference"] == pytest.approx(75.0)
    assert result["increment"] == pytest.approx(25.0)


# --- Tests simulation_backend.py ---


def should_linear_backend_have_low_confidence() -> None:
    """Le backend linéaire v1 a une confiance 'low'."""
    backend = LinearGrowthBackend()
    assert backend.confidence() == ConfidenceLevel.low
    assert len(backend.sources()) >= 1
    assert len(backend.assumptions()) >= 1


def should_calibrated_backend_have_medium_confidence() -> None:
    """Le backend calibré IGN a une confiance 'medium'."""
    backend = CalibratedGrowthBackend()
    assert backend.confidence() == ConfidenceLevel.medium
    assert any("IGN" in s for s in backend.sources())
    assert len(backend.assumptions()) >= 4


def should_calibrated_backend_project_volume() -> None:
    """Le backend calibré projette le volume via growth_models."""
    backend = CalibratedGrowthBackend()
    result = backend.simulate_growth(
        "Fagus sylvatica",
        initial_state={"volume": 100.0},
        horizon_years=10,
    )
    assert result["final_volume"] == pytest.approx(170.0)
    assert result["capped"] is False
    assert "IGN" in result["volume_source"]


def should_calibrated_backend_project_circumference() -> None:
    """Le backend calibré projette la circonférence."""
    backend = CalibratedGrowthBackend()
    result = backend.simulate_growth(
        "Pinus sylvestris",
        initial_state={"circumference": 50.0},
        horizon_years=10,
    )
    assert result["final_circumference"] == pytest.approx(75.0)


def should_calibrated_backend_apply_density_factor() -> None:
    """Le backend calibré applique le facteur de densité."""
    backend = CalibratedGrowthBackend()
    result = backend.simulate_growth(
        "Fagus sylvatica",
        initial_state={"volume": 100.0},
        horizon_years=10,
        parameters={"density_factor": 0.5},
    )
    assert result["annual_volume_increment"] == pytest.approx(3.5)


def should_calibrated_backend_raise_for_unknown_species() -> None:
    """Le backend calibré lève pour une essence non calibrée."""
    backend = CalibratedGrowthBackend()
    with pytest.raises(SimulationBackendError, match="non calibrée"):
        backend.simulate_growth("Unknown", {"volume": 100.0}, 10)


def should_calibrated_backend_raise_for_empty_state() -> None:
    """Le backend calibré exige au moins volume ou circonférence > 0."""
    backend = CalibratedGrowthBackend()
    with pytest.raises(SimulationBackendError, match="initial_state"):
        backend.simulate_growth("Fagus sylvatica", {}, 10)


def should_capsis_backend_raise_not_implemented() -> None:
    """Le backend CAPSIS lève NotImplementedError en v1."""
    backend = CapsisBackend()
    assert backend.confidence() == ConfidenceLevel.high
    with pytest.raises(NotImplementedError, match="non implémenté"):
        backend.simulate_growth("Fagus sylvatica", {"volume": 100.0}, 10)


def should_capsis_backend_document_source() -> None:
    """Le backend CAPSIS documente sa source (Dufour-Kowalski 2012)."""
    backend = CapsisBackend()
    sources = backend.sources()
    assert any("Dufour-Kowalski" in s or "Capsis" in s for s in sources)
    assert any("Java" in a or "INRAE" in a for a in backend.assumptions())
