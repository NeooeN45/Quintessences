"""Tests unitaires — Recommendation Engine.

Vérifie la génération de recommandations contournables avec
alternatives, et l'enregistrement des décisions du forestier.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from gsie_api.engines.recommendation.engine import (
    RecommandationIntrouvableError,
    RecommendationEngine,
)
from gsie_api.engines.recommendation.schemas import (
    DecisionForestier,
    ForestierDecision,
    ObjectifForestier,
    RecommendationRequest,
    TypeAction,
)
from gsie_api.infrastructure.models.enums import DiagnosticGlobalState
from tests.unit.aide_recommendation import SessionDiagnosticFictif


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
    return RecommendationEngine(SessionDiagnosticFictif())


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
    engine = RecommendationEngine(SessionDiagnosticFictif())
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
    """Une décision 'accepte' est enregistrée, et le statut le dit sans mentir.

    Le statut valait `enregistre` alors que la méthode ne persistait rien — un
    accusé de conservation pour une trace inexistante, plus dommageable que
    l'absence d'accusé : le forestier cesse de tenir la sienne. Il a valu
    `recu_non_persiste` le temps que la persistance arrive.

    Elle est là, et l'accusé porte désormais l'identifiant de la trace écrite :
    sans lui, le forestier ne peut pas la retrouver. L'écriture elle-même est
    vérifiée sur PostgreSQL par
    `tests/integration/test_recommendation_persistance.py` — le stub avale les
    écritures et ne prouve rien de ce côté.
    """
    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.ACCEPTE,
        date_decision=datetime.now(UTC),
    )
    result = await engine.record_decision(decision)
    assert result["statut"] == "enregistre"
    assert result["decision"] == "accepte"
    assert "avertissement" not in result, (
        "l'avertissement de non-conservation subsiste alors que la décision est "
        "persistée — il induirait le forestier en erreur dans l'autre sens"
    )
    assert result["decision_id"], "l'accusé ne permet pas de retrouver la trace"


@pytest.mark.asyncio
async def should_refuse_a_decision_citing_an_unknown_recommendation() -> None:
    """Une décision qui cite une recommandation inexistante est refusée.

    Enregistrer produirait une trace inexploitable : on saurait qu'un forestier
    a refusé quelque chose, sans pouvoir dire quoi. La jonction
    `decision_recommendation` porte d'ailleurs une clé étrangère — PostgreSQL
    refuserait de son côté, mais en erreur serveur plutôt qu'en refus explicite.
    """
    moteur = RecommendationEngine(SessionDiagnosticFictif(recommandation_existe=False))
    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.REFUSE,
        date_decision=datetime.now(UTC),
    )

    with pytest.raises(RecommandationIntrouvableError):
        await moteur.record_decision(decision)


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


# --- L'etat du peuplement pilote la sortie ---


@pytest.mark.parametrize(
    "etat_degrade",
    [DiagnosticGlobalState.deperissement, DiagnosticGlobalState.critique],
)
@pytest.mark.asyncio
async def should_refuse_intervention_on_degraded_stand(
    etat_degrade: DiagnosticGlobalState,
) -> None:
    """Un peuplement dégradé ne reçoit pas le conseil du peuplement sain.

    Défaut reproduit avant correction : le moteur dérivait l'action du seul
    objectif forestier. Un peuplement diagnostiqué `critique`, avec 45 % de
    mortalité dans son contenu, recevait mot pour mot « éclaircie modérée
    (prélèvement 25 %) pour favoriser la croissance » — le conseil du peuplement
    sain, à l'identique.

    Le moteur n'arbitre pas quelle intervention convient à un peuplement
    dégradé : ce serait une table de conversion inventée (`ADR-009`). Il
    constate que son mapping ne couvre pas le cas et le dit.
    """
    moteur = RecommendationEngine(SessionDiagnosticFictif(etat_global=etat_degrade))
    requete = RecommendationRequest(
        requete_id=uuid4(),
        diagnostic_id=uuid4(),
        objectif_forestier=ObjectifForestier.PRODUCTION,
        alternatives_demandees=True,
    )

    ensemble = await moteur.recommend(requete)

    types = {reco.type_action for reco in ensemble.recommandations}
    assert types == {TypeAction.ATTENTE_SURVEILLANCE}, (
        f"actions proposées sur un peuplement {etat_degrade.value} : " f"{[t.value for t in types]}"
    )

    reco = ensemble.recommandations[0]
    # Le motif doit etre lisible par le forestier, pas seulement encode dans le
    # type d'action : c'est lui qui decide (`GSIE-CON-001`), il lui faut le
    # pourquoi.
    assert etat_degrade.value in reco.description
    assert any(
        etat_degrade.value in f for f in reco.justification.facteurs_limitants
    ), "l'état du peuplement ne figure pas dans les facteurs limitants"
    assert not reco.alternatives, (
        "des alternatives sont proposées alors qu'aucune règle ne couvre le cas "
        "— elles seraient inventées"
    )


@pytest.mark.asyncio
async def should_still_recommend_on_healthy_stand() -> None:
    """Le peuplement sain continue de recevoir une action.

    Sans ce contrôle, refuser sur tous les états ferait passer le test
    précédent : « ne jamais rien proposer » satisfait « ne pas proposer sur un
    peuplement dégradé ».
    """
    moteur = RecommendationEngine(SessionDiagnosticFictif(etat_global=DiagnosticGlobalState.sain))
    requete = RecommendationRequest(
        requete_id=uuid4(),
        diagnostic_id=uuid4(),
        objectif_forestier=ObjectifForestier.PRODUCTION,
        alternatives_demandees=True,
    )

    ensemble = await moteur.recommend(requete)

    assert ensemble.recommandations[0].type_action == TypeAction.ECLAIRCIE
    assert ensemble.recommandations[0].alternatives, (
        "les alternatives restent dues sur un peuplement dont l'état permet " "l'intervention"
    )


# ===========================================================================
# Couverture complémentaire — lignes 187, 415, 427
# ===========================================================================


@pytest.mark.asyncio
async def should_raise_diagnostic_introuvable_when_id_missing() -> None:
    """_diagnostic doit lever DiagnosticIntrouvableError si introuvable."""
    from unittest.mock import AsyncMock

    from gsie_api.engines.recommendation.engine import DiagnosticIntrouvableError

    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    engine = RecommendationEngine(session)

    with pytest.raises(DiagnosticIntrouvableError, match="introuvable"):
        await engine._diagnostic(uuid4())


@pytest.mark.asyncio
async def should_create_forestier_agent_when_forestier_id_provided() -> None:
    """_agent_forestier doit créer un agent quand forestier_id est fourni."""
    from unittest.mock import AsyncMock, MagicMock

    session = AsyncMock()
    session.get = AsyncMock(return_value=None)  # Resource n'existe pas
    session.add = MagicMock()
    session.flush = AsyncMock()
    engine = RecommendationEngine(session)

    forestier_id = uuid4()
    result = await engine._agent_forestier(forestier_id)
    assert result == forestier_id
    # session.add doit avoir été appelé pour créer la resource + l'agent
    assert session.add.call_count >= 2


@pytest.mark.asyncio
async def should_return_agent_id_when_resource_already_exists() -> None:
    """_agent doit retourner l'agent_id si la resource existe déjà."""
    from unittest.mock import AsyncMock, MagicMock

    from gsie_api.infrastructure.models.base import ResourceModel

    session = AsyncMock()
    # Resource existe déjà
    existing = MagicMock(spec=ResourceModel)
    session.get = AsyncMock(return_value=existing)
    session.add = MagicMock()
    session.flush = AsyncMock()
    engine = RecommendationEngine(session)

    agent_id = uuid4()
    result = await engine._agent(agent_id, nom="Test", type_agent=MagicMock())
    assert result == agent_id
    # session.add ne doit pas avoir été appelé
    session.add.assert_not_called()


# --- Garde : la persistance des recommandations est traçable (GSIE-CON-005)
#
# Ces tests tuent les mutations `recommandations_non_persistees`,
# `alternatives_non_persistees`, `jonction_decision_perdue` et
# `rationale_inventee` qui survivaient parce que `SessionDiagnosticFictif`
# avale les écritures. La `SessionEspion` enregistre les appels.


@pytest.mark.asyncio
async def should_persist_recommendations_when_generated() -> None:
    """Les recommandations produites doivent être persistées en session."""
    from gsie_api.infrastructure.models.reasoning import RecommendationModel
    from tests.unit.aide_recommendation import SessionEspion

    session = SessionEspion()
    engine = RecommendationEngine(session)
    await engine.recommend(_make_request())
    # Au moins une RecommendationModel doit être ajoutée à la session
    recs = [a for a in session.ajouts if isinstance(a, RecommendationModel)]
    assert len(recs) >= 1


@pytest.mark.asyncio
async def should_persist_alternatives_when_requested() -> None:
    """Les alternatives doivent être persistées au même titre que la principale."""
    from gsie_api.infrastructure.models.reasoning import RecommendationModel
    from tests.unit.aide_recommendation import SessionEspion

    session = SessionEspion()
    engine = RecommendationEngine(session)
    await engine.recommend(_make_request(alternatives=True))
    # La principale + au moins une alternative doivent être persistées
    recs = [a for a in session.ajouts if isinstance(a, RecommendationModel)]
    assert len(recs) >= 2, (
        f"attendu >= 2 recommandations persistées (principale + alternative), " f"got {len(recs)}"
    )


@pytest.mark.asyncio
async def should_link_decision_to_correct_recommendation_when_recorded() -> None:
    """La jonction decision_recommendation doit pointer vers la recommandation citée."""
    from tests.unit.aide_recommendation import SessionEspion

    session = SessionEspion()
    engine = RecommendationEngine(session)
    reco_id = uuid4()
    decision = ForestierDecision(
        recommandation_id=reco_id,
        decision=DecisionForestier.REFUSE,
        justification_forestier="Test",
        date_decision=datetime.now(UTC),
    )
    await engine.record_decision(decision)
    # L'insert dans decision_recommendation doit contenir recommendation_id=reco_id
    # (pas decision_id — la mutation `jonction_decision_perdue` remplace l'un par l'autre)
    # SQLAlchemy compile les UUID sans tirets : on compare donc en hex.
    reco_hex = reco_id.hex
    found = False
    for ins in session.insertions:
        if ins is None:
            continue
        compiled = str(ins.compile(compile_kwargs={"literal_binds": True}))
        if "decision_recommendation" in compiled and reco_hex in compiled:
            found = True
            break
    assert found, (
        "la jonction decision_recommendation doit contenir recommendation_id="
        f"{reco_id}, aucune insertion correspondante trouvée"
    )


def should_record_default_rationale_when_no_justification_provided() -> None:
    """Le rationale par défaut doit dire « Aucune justification », pas inventer.

    Tuer la mutation `rationale_inventee` qui remplace le texte neutre par une
    explication plausible que le forestier n'a jamais donnée (ADR-009).
    """
    from gsie_api.engines.recommendation.engine import _rationale

    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.REFUSE,
        date_decision=datetime.now(UTC),
    )
    rationale = _rationale(decision)
    assert "Aucune justification fournie" in rationale
    assert "inadaptée" not in rationale.lower()


@pytest.mark.asyncio
async def should_return_decision_id_matching_persisted_model() -> None:
    """L'identifiant retourné correspond à la ligne DecisionModel écrite.

    Sans cette vérification, l'accusé rend un ``decision_id`` qui ne mène à
    aucune ligne : le forestier ne peut pas retrouver sa trace, et croit
    l'avoir.
    """
    from gsie_api.infrastructure.models.reasoning import DecisionModel
    from tests.unit.aide_recommendation import SessionEspion

    # Arrange — session espion qui enregistre les écritures
    session = SessionEspion()
    engine = RecommendationEngine(session)
    decision = ForestierDecision(
        recommandation_id=uuid4(),
        decision=DecisionForestier.ACCEPTE,
        date_decision=datetime.now(UTC),
    )

    # Act
    result = await engine.record_decision(decision)
    returned_id_str = result["decision_id"]

    # Assert — le DecisionModel persisté doit porter le même id que l'accusé
    decision_models = [obj for obj in session.ajouts if isinstance(obj, DecisionModel)]
    assert len(decision_models) == 1, "exactement un DecisionModel doit être persisté"
    assert str(decision_models[0].id) == returned_id_str, (
        "l'id du DecisionModel persisté ne correspond pas à l'accusé rendu — "
        "le forestier ne peut pas retrouver sa trace"
    )
