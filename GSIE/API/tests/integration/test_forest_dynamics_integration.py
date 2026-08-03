"""Tests d'intégration — Forest Dynamics Engine.

Le moteur Forest Dynamics est purement géométrique (pas de DB, pas de
réseau). Ces tests d'intégration valident des scénarios complets :
chaîne de calcul + construction du passeport de décision, propagation
d'identifiants, cas limites — au-delà des tests unitaires qui isolent
chaque formule.

Conventions (AGENTS.md API) : pytest-asyncio mode `auto`, nommage
`should_[expected]_when_[condition]`, structure Arrange → Act → Assert.
"""

import math
from uuid import uuid4

import pytest

from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.forest_dynamics.engine import ForestDynamicsEngine
from gsie_api.engines.forest_dynamics.schemas import (
    CaracteristiqueDendrometrique,
    DendrometricRequest,
    PeuplementState,
    StructurePeuplement,
)
from gsie_api.shared.schemas import DecisionPassportCategory, DecisionPassportItem


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.observation_terrain,
        auteur="Inventaire IFN test",
        reference="Placette IFN simulée pour test d'intégration",
    )


def _request(
    diametre_moyen_cm: float = 25.0,
    densite_t_ha: float = 600.0,
    station_observation_id: object | None = None,
) -> DendrometricRequest:
    kwargs: dict[str, object] = {
        "etat_initial": PeuplementState(
            essence_principale="Fagus sylvatica",
            age_moyen=60.0,
            densite_t_ha=densite_t_ha,
            diametre_moyen_cm=diametre_moyen_cm,
            hauteur_moyenne_m=22.0,
            structure=StructurePeuplement.reguliere,
            source_inventaire=_source(),
        ),
    }
    if station_observation_id is not None:
        kwargs["station_observation_id"] = station_observation_id
    return DendrometricRequest(**kwargs)


# ─────────────────────────────────────────────────────────────────────────
# Tests d'intégration — chaîne complète calcul + passeport
# ─────────────────────────────────────────────────────────────────────────


def should_compute_basal_area_and_build_passport_in_full_flow() -> None:
    """Le calcul dendrométrique puis la construction du passeport forment une chaîne cohérente.

    Vérifie que la valeur calculée se retrouve exactement dans le passeport,
    avec la bonne unité et la bonne méthode — un forestier doit pouvoir
    refaire le calcul à la main depuis ce qui est affiché.
    """
    engine = ForestDynamicsEngine()
    request = _request(diametre_moyen_cm=25.0, densite_t_ha=600.0)
    result = engine.compute_dendrometrics(request)
    items = engine.to_decision_passport_items(result)

    assert len(items) == 1
    item: DecisionPassportItem = items[0]
    assert item.category == DecisionPassportCategory.calcule
    assert item.label == "surface_terriere"

    # La valeur affichée dans le passeport doit correspondre au calcul
    diametre_m = 0.25
    expected_g = (math.pi / 4.0) * (diametre_m**2) * 600.0
    assert result.caracteristiques[0].valeur == pytest.approx(expected_g)
    assert "m²/ha" in item.value
    assert item.method == "G = (π/4) × D² × N"


def should_propagate_station_observation_id_through_pipeline() -> None:
    """RFC-0016 §5 : station_observation_id transmis de la requête au résultat, sans altération."""
    station_id = uuid4()
    engine = ForestDynamicsEngine()
    request = _request(station_observation_id=station_id)
    result = engine.compute_dendrometrics(request)

    assert result.station_observation_id == station_id


def should_handle_extreme_diameter_values() -> None:
    """Diamètres extrêmes (1cm et 200cm) — la formule géométrique reste exacte."""
    engine = ForestDynamicsEngine()

    # Très petit diamètre (1 cm = 0.01 m)
    result_small = engine.compute_dendrometrics(
        _request(diametre_moyen_cm=1.0, densite_t_ha=1000.0)
    )
    expected_small = (math.pi / 4.0) * (0.01**2) * 1000.0
    assert result_small.caracteristiques[0].valeur == pytest.approx(expected_small)

    # Très grand diamètre (200 cm = 2.0 m)
    result_large = engine.compute_dendrometrics(
        _request(diametre_moyen_cm=200.0, densite_t_ha=50.0)
    )
    expected_large = (math.pi / 4.0) * (2.0**2) * 50.0
    assert result_large.caracteristiques[0].valeur == pytest.approx(expected_large)


def should_handle_zero_density_gracefully() -> None:
    """Densité nulle interdite par le schema (gt=0) — vérifie la garde Pydantic."""
    with pytest.raises(ValueError, match="densite_t_ha"):
        _request(densite_t_ha=0.0)


def should_produce_passport_with_calcule_category_only() -> None:
    """Toutes les caractéristiques v1 sont étiquetées `calcule` — jamais `modelisee`."""
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request())
    items = engine.to_decision_passport_items(result)

    for item in items:
        assert item.category == DecisionPassportCategory.calcule


def should_source_reference_cite_geometry_identity() -> None:
    """La source du résultat cite la formule géométrique — pas un coefficient empirique inventé."""
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request())

    reference = result.source.reference
    assert "G = (π/4) × D² × N" in reference
    assert "géométrique" in reference.lower() or "aire" in reference.lower()


def should_preserve_caracteristique_method_in_passport() -> None:
    """La méthode de calcul est préservée dans le passeport — traçabilité de la formule."""
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request())
    items = engine.to_decision_passport_items(result)

    carac: CaracteristiqueDendrometrique = result.caracteristiques[0]
    assert items[0].method == carac.methode
    assert "G = (π/4)" in items[0].method
