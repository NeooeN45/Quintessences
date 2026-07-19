"""Tests unitaires — Forest Dynamics Engine.

Purement géométrique (identité mathématique, pas d'appel réseau,
pas de persistance) — voir docstring engine.py pour le périmètre v1
et les raisons documentées du non-périmètre (volume, projection).
Couvre aussi (RFC-0016 §5 Phase B, point 5) le passthrough de
`station_observation_id` et la construction du passeport de décision.
"""

import math
from uuid import uuid4

import pytest

from gsie_api.engines.evidence.schemas import SourceReference, SourceType
from gsie_api.engines.forest_dynamics.engine import ForestDynamicsEngine
from gsie_api.engines.forest_dynamics.schemas import (
    DendrometricRequest,
    PeuplementState,
    StructurePeuplement,
)
from gsie_api.shared.schemas import DecisionPassportCategory


def _source() -> SourceReference:
    return SourceReference(
        type_source=SourceType.observation_terrain,
        auteur="Inventaire test",
        reference="Placette IFN simulée pour test unitaire",
    )


def _request(diametre_moyen_cm: float = 20.0, densite_t_ha: float = 500.0) -> DendrometricRequest:
    return DendrometricRequest(
        etat_initial=PeuplementState(
            essence_principale="Quercus petraea",
            age_moyen=40.0,
            densite_t_ha=densite_t_ha,
            diametre_moyen_cm=diametre_moyen_cm,
            hauteur_moyenne_m=18.0,
            structure=StructurePeuplement.reguliere,
            source_inventaire=_source(),
        )
    )


def test_basal_area_matches_exact_circle_geometry():
    """G doit correspondre exactement à (π/4) × D² × N — vérifiable à la main."""
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request(diametre_moyen_cm=20.0, densite_t_ha=500.0))

    diametre_m = 0.20
    expected = (math.pi / 4.0) * (diametre_m**2) * 500.0

    assert len(result.caracteristiques) == 1
    carac = result.caracteristiques[0]
    assert carac.nom == "surface_terriere"
    assert carac.valeur == pytest.approx(expected)
    assert carac.unite == "m²/ha"


def test_basal_area_scales_with_density():
    """Doubler la densité de tiges doit doubler la surface terrière (linéarité de la formule)."""
    engine = ForestDynamicsEngine()
    result_1x = engine.compute_dendrometrics(_request(densite_t_ha=400.0))
    result_2x = engine.compute_dendrometrics(_request(densite_t_ha=800.0))

    assert result_2x.caracteristiques[0].valeur == pytest.approx(
        2 * result_1x.caracteristiques[0].valeur
    )


def test_basal_area_scales_with_diameter_squared():
    """Doubler le diamètre doit quadrupler la surface terrière (loi en D²)."""
    engine = ForestDynamicsEngine()
    result_1x = engine.compute_dendrometrics(_request(diametre_moyen_cm=15.0))
    result_2x = engine.compute_dendrometrics(_request(diametre_moyen_cm=30.0))

    assert result_2x.caracteristiques[0].valeur == pytest.approx(
        4 * result_1x.caracteristiques[0].valeur
    )


def test_result_preserves_requete_and_peuplement_id():
    """Le résultat doit référencer les mêmes UUID que la requête (traçabilité)."""
    engine = ForestDynamicsEngine()
    request = _request()
    result = engine.compute_dendrometrics(request)

    assert result.requete_id == request.requete_id
    assert result.peuplement_id == request.peuplement_id


def test_no_volume_or_trajectory_in_v1_result():
    """Garde-fou ADR-007 : v1 ne doit produire ni volume ni trajectoire de croissance inventés."""
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request())

    noms = {c.nom for c in result.caracteristiques}
    assert "volume_approche" not in noms
    assert "trajectoire" not in noms
    assert noms == {"surface_terriere"}


def test_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(ForestDynamicsEngine.version()) > 0


def test_station_observation_id_is_none_by_default():
    """Sans référence de station fournie, le résultat n'en invente pas une."""
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request())
    assert result.station_observation_id is None


def test_station_observation_id_passes_through_to_result():
    """RFC-0016 §5 Phase B point 5 : la référence à la station diagnostiquée

    doit être transmise telle quelle, sans être résolue ni modifiée par
    le moteur (fonction pure, aucune session DB en v1).
    """
    engine = ForestDynamicsEngine()
    station_id = uuid4()
    request = DendrometricRequest(
        station_observation_id=station_id,
        etat_initial=PeuplementState(
            essence_principale="Quercus petraea",
            age_moyen=40.0,
            densite_t_ha=500.0,
            diametre_moyen_cm=20.0,
            hauteur_moyenne_m=18.0,
            structure=StructurePeuplement.reguliere,
            source_inventaire=_source(),
        ),
    )
    result = engine.compute_dendrometrics(request)
    assert result.station_observation_id == station_id


def test_to_decision_passport_items_produces_calcule_category():
    """RFC-0016 §3.4 : une surface terrière calculée est toujours étiquetée

    `calcule`, jamais affichée comme une mesure directe ou un modèle.
    """
    engine = ForestDynamicsEngine()
    result = engine.compute_dendrometrics(_request())
    items = ForestDynamicsEngine.to_decision_passport_items(result)

    assert len(items) == 1
    assert items[0].category == DecisionPassportCategory.calcule
    assert items[0].label == "surface_terriere"
    assert items[0].method == "G = (π/4) × D² × N"
