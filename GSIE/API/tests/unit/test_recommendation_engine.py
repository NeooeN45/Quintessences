"""Tests unitaires — Recommendation Engine.

Vérifie la génération de recommandations contournables avec
alternatives, et l'enregistrement des décisions du forestier.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.recommendation.schemas import (
    DecisionForestier,
    ForestierDecision,
    ObjectifForestier,
    RecommendationRequest,
    TypeAction,
)


def _make_request(
    objectif: ObjectifForestier = ObjectifForestier.REBOISEMENT,
    alternatives: bool = True,
) -> RecommendationRequest:
    return RecommendationRequest(
        requete_id=uuid4(),
        diagnostic_id=uuid4(),
        objectif_forestier=objectif,
        alternatives_demandees=alternatives,
    )


@pytest.fixture
def engine() -> RecommendationEngine:
    return RecommendationEngine()


# --- Tests génération ---


@pytest.mark.asyncio
async def should_generate_non_empty_recommendation_set(engine: RecommendationEngine) -> None:
    """Le moteur ne retourne jamais un ensemble vide (contrat §5)."""
    request = _make_request()
    result = await engine.recommend(request)
    assert len(result.recommandations) >= 1


@pytest.mark.asyncio
async def should_generate_alternatives_when_requested(engine: RecommendationEngine) -> None:
    """Des alternatives sont systématiquement proposées si demandées."""
    request = _make_request(alternatives=True)
    result = await engine.recommend(request)
    principale = result.recommandations[0]
    assert len(principale.alternatives) >= 1


@pytest.mark.asyncio
async def should_not_generate_alternatives_when_not_requested(engine: RecommendationEngine) -> None:
    """Aucune alternative si alternatives_demandees=False."""
    request = _make_request(alternatives=False)
    result = await engine.recommend(request)
    principale = result.recommandations[0]
    assert len(principale.alternatives) == 0


@pytest.mark.asyncio
async def should_return_contournable_recommendations(engine: RecommendationEngine) -> None:
    """Toute recommandation est contournable (GSIE-CON-001)."""
    request = _make_request()
    result = await engine.recommend(request)
    for reco in result.recommandations:
        assert reco.contournable is True


@pytest.mark.asyncio
async def should_return_justified_recommendations(engine: RecommendationEngine) -> None:
    """Toute recommandation a une justification avec sources (GSIE-CON-004)."""
    request = _make_request()
    result = await engine.recommend(request)
    for reco in result.recommandations:
        assert reco.justification is not None
        assert len(reco.justification.sources) >= 1
        assert len(reco.justification.facteurs_limitants) >= 1


@pytest.mark.asyncio
async def should_map_objectif_to_action_type() -> None:
    """L'objectif forestier détermine le type d'action de la recommandation principale."""
    engine = RecommendationEngine()
    mapping = {
        ObjectifForestier.REBOISEMENT: TypeAction.PLANTATION,
        ObjectifForestier.PRODUCTION: TypeAction.ECLAIRCIE,
        ObjectifForestier.PROTECTION: TypeAction.PROTECTION,
        ObjectifForestier.BIODIVERSITE: TypeAction.REGENERATION,
    }
    for objectif, expected_action in mapping.items():
        request = _make_request(objectif=objectif)
        result = await engine.recommend(request)
        assert result.recommandations[0].type_action == expected_action


@pytest.mark.asyncio
async def should_set_confidence_in_valid_range(engine: RecommendationEngine) -> None:
    """Le niveau de confiance est dans [0, 1]."""
    request = _make_request()
    result = await engine.recommend(request)
    for reco in result.recommandations:
        assert 0.0 <= reco.niveau_confiance <= 1.0


@pytest.mark.asyncio
async def should_reference_diagnostic_in_justification(engine: RecommendationEngine) -> None:
    """La justification référence le diagnostic source (traçabilité)."""
    request = _make_request()
    result = await engine.recommend(request)
    for reco in result.recommandations:
        assert reco.justification.diagnostic_ref == request.diagnostic_id


# --- Tests décision forestier ---


@pytest.mark.asyncio
async def should_record_accepte_decision(engine: RecommendationEngine) -> None:
    """Une décision 'accepte' est enregistrée avec accusé."""
    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.ACCEPTE,
        date_decision=datetime.now(UTC),
    )
    result = await engine.record_decision(decision)
    assert result["statut"] == "enregistre"
    assert result["decision"] == "accepte"


@pytest.mark.asyncio
async def should_record_refuse_decision(engine: RecommendationEngine) -> None:
    """Une décision 'refuse' est enregistrée."""
    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.REFUSE,
        justification_forestier="Risque de dépérissement",
        date_decision=datetime.now(UTC),
    )
    result = await engine.record_decision(decision)
    assert result["decision"] == "refuse"


@pytest.mark.asyncio
async def should_record_modifie_decision_with_modifications(engine: RecommendationEngine) -> None:
    """Une décision 'modifie' avec modifications est enregistrée."""
    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.MODIFIE,
        modifications={"densite": "1200"},
        date_decision=datetime.now(UTC),
    )
    result = await engine.record_decision(decision)
    assert result["decision"] == "modifie"


# --- Tests invariants schéma (déjà couverts par test_recommendation_schemas.py) ---


@pytest.mark.asyncio
async def should_generate_distinct_alternative_ids(engine: RecommendationEngine) -> None:
    """Les alternatives ont des identifiants distincts."""
    request = _make_request(alternatives=True)
    result = await engine.recommend(request)
    principale = result.recommandations[0]
    ids = [alt.recommandation_id for alt in principale.alternatives]
    assert len(ids) == len(set(ids))
