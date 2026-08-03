"""Tests d'intégration — la trace d'une recommandation et de sa suite existe.

`record_decision` répondait « enregistré » en n'écrivant rien : le forestier qui
refusait une recommandation lisait un accusé de conservation pour une trace
n'existant que dans une ligne de log. `GSIE-CON-005` exige la traçabilité, et
« aucune décision perdue » n'est pas satisfait par un message qui l'affirme.

Le métamodèle prévoyait cette écriture depuis l'origine — types `recommendation`
et `decision` (`ADR-002`), jonction `decision_recommendation` — sans qu'aucun
code l'emprunte. Rien n'a donc été ajouté au métamodèle, et aucune migration
n'était nécessaire : les tables existaient déjà.

Ce module est le seul qui **établit** la persistance. Les tests unitaires
emploient `SessionDiagnosticFictif`, dont les méthodes d'écriture avalent tout
sans conserver : ils vérifient le mapping objectif → action sans base, et ne
prouvent rien de ce côté. Sans ce module-là, le stub masquerait exactement ce
qu'il simplifie — l'erreur déjà commise dans ce dépôt, où des tests SQLite
laissaient passer des violations de clé étrangère que PostgreSQL refusait.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.recommendation.engine import (
    RecommandationIntrouvableError,
    RecommendationEngine,
)
from gsie_api.engines.recommendation.schemas import (
    DecisionForestier,
    ForestierDecision,
    ObjectifForestier,
    RecommendationRequest,
)
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.diagnostic import DiagnosticModel
from gsie_api.infrastructure.models.enums import (
    DiagnosticGlobalState,
    DiagnosticType,
    DiagnosticValidationStatus,
    EvidenceLevel,
)
from gsie_api.infrastructure.models.junctions import decision_recommendation
from gsie_api.infrastructure.models.prov import AgentModel
from gsie_api.infrastructure.models.reasoning import DecisionModel, RecommendationModel
from tests.conftest import requires_docker

pytestmark = requires_docker

_CONFIANCE = 0.42


async def _diagnostic(session: AsyncSession) -> UUID:
    """Insère un diagnostic sain, racine `resource` comprise (ADR-001)."""
    identifiant = uuid4()
    session.add(ResourceModel(id=identifiant, type="diagnostic"))
    await session.flush()
    session.add(
        DiagnosticModel(
            id=identifiant,
            requete_origine=uuid4(),
            station_id=uuid4(),
            type_diagnostic=DiagnosticType.stationnel,
            etat_global=DiagnosticGlobalState.sain,
            confiance=_CONFIANCE,
            evidence_level_plancher=EvidenceLevel.b,
            statut_validation=DiagnosticValidationStatus.brouillon,
            date_diagnostic=datetime.now(UTC),
            contenu={"origine": "test de persistance"},
        )
    )
    await session.flush()
    return identifiant


def _requete(diagnostic_id: UUID) -> RecommendationRequest:
    return RecommendationRequest(
        requete_id=uuid4(),
        diagnostic_id=diagnostic_id,
        objectif_forestier=ObjectifForestier.PRODUCTION,
        alternatives_demandees=True,
    )


@pytest.mark.asyncio
async def test_les_alternatives_sont_persistees_autant_que_la_principale(
    db_session: AsyncSession,
) -> None:
    """Chaque recommandation produite existe en base, alternatives comprises.

    Le forestier peut retenir une alternative : sa décision doit pouvoir la
    citer. N'écrire que la principale rendrait ce choix-là intraçable, alors que
    proposer des alternatives est un principe fondateur.
    """
    ensemble = await RecommendationEngine(db_session).recommend(
        _requete(await _diagnostic(db_session))
    )

    attendus = {
        candidate.recommandation_id
        for reco in ensemble.recommandations
        for candidate in (reco, *reco.alternatives)
    }
    assert len(attendus) > 1, "aucune alternative produite : le test ne prouverait rien"

    trouves = set(
        (
            await db_session.execute(
                select(RecommendationModel.id).where(RecommendationModel.id.in_(attendus))
            )
        )
        .scalars()
        .all()
    )
    assert trouves == attendus, f"non persistées : {sorted(attendus - trouves)}"


@pytest.mark.asyncio
async def test_la_confiance_persistee_est_celle_du_diagnostic(
    db_session: AsyncSession,
) -> None:
    """La colonne `confidence` porte la confiance du diagnostic, pas une constante."""
    ensemble = await RecommendationEngine(db_session).recommend(
        _requete(await _diagnostic(db_session))
    )
    principale = ensemble.recommandations[0]

    ligne = await db_session.get(RecommendationModel, principale.recommandation_id)

    assert ligne is not None
    assert ligne.confidence == pytest.approx(_CONFIANCE)


@pytest.mark.asyncio
async def test_la_decision_est_ecrite_et_reliee_a_sa_recommandation(
    db_session: AsyncSession,
) -> None:
    """La décision existe, nomme son auteur, et la jonction la relie.

    Trois vérifications distinctes, parce que trois choses peuvent manquer
    séparément : la ligne `decision`, l'Agent qui la porte — `decided_by` est
    NOT NULL et référence `resource(id)` — et l'entrée de jonction sans laquelle
    on ne sait plus à quoi la décision répondait.
    """
    ensemble = await RecommendationEngine(db_session).recommend(
        _requete(await _diagnostic(db_session))
    )
    cible = ensemble.recommandations[0].recommandation_id
    forestier = uuid4()

    accuse = await RecommendationEngine(db_session).record_decision(
        ForestierDecision(
            recommandation_id=cible,
            decision=DecisionForestier.REFUSE,
            justification_forestier="Peuplement déjà éclairci l'an dernier",
            date_decision=datetime.now(UTC),
        ),
        forestier_id=forestier,
    )

    assert accuse["statut"] == "enregistre"
    decision = await db_session.get(DecisionModel, UUID(accuse["decision_id"]))
    assert decision is not None, "l'accusé annonce une trace qui n'existe pas"
    assert decision.decision_text == "refuse"
    assert "déjà éclairci" in decision.rationale

    # L'auteur est materialise en Agent : sans lui, la cle etrangere refuse.
    agent = await db_session.get(AgentModel, forestier)
    assert agent is not None, "l'auteur de la décision n'existe pas comme Agent"

    liens = (
        (
            await db_session.execute(
                select(decision_recommendation.c.recommendation_id).where(
                    decision_recommendation.c.decision_id == decision.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert list(liens) == [cible], (
        "la jonction ne relie pas la décision à sa recommandation — on ne sait "
        "plus à quoi le forestier a répondu"
    )


@pytest.mark.asyncio
async def test_une_decision_sans_justification_le_consigne_sans_en_inventer(
    db_session: AsyncSession,
) -> None:
    """L'absence de justification est enregistrée comme telle.

    `decision.rationale` est NOT NULL, alors que `justification_forestier` est
    délibérément facultatif : « exiger une explication du forestier reviendrait
    à lui demander de se justifier devant l'outil » (`GSIE-CON-001`).

    Les deux exigences se concilient en consignant un fait, pas une raison.
    Écrire une explication plausible serait l'invention que `ADR-009` interdit —
    et elle serait relue comme la parole du forestier.
    """
    ensemble = await RecommendationEngine(db_session).recommend(
        _requete(await _diagnostic(db_session))
    )

    accuse = await RecommendationEngine(db_session).record_decision(
        ForestierDecision(
            recommandation_id=ensemble.recommandations[0].recommandation_id,
            decision=DecisionForestier.REFUSE,
            date_decision=datetime.now(UTC),
        )
    )

    decision = await db_session.get(DecisionModel, UUID(accuse["decision_id"]))
    assert decision is not None
    assert (
        "Aucune justification fournie" in decision.rationale
    ), f"rationale inventée : {decision.rationale!r}"


@pytest.mark.asyncio
async def test_une_decision_sur_une_recommandation_absente_est_refusee(
    db_session: AsyncSession,
) -> None:
    """Le refus est explicite, jamais une violation de clé étrangère.

    La jonction porte une clé étrangère : PostgreSQL refuserait de son côté,
    mais en erreur serveur. Un refus métier nommé permet à l'appelant de
    corriger.
    """
    with pytest.raises(RecommandationIntrouvableError):
        await RecommendationEngine(db_session).record_decision(
            ForestierDecision(
                recommandation_id=uuid4(),
                decision=DecisionForestier.ACCEPTE,
                date_decision=datetime.now(UTC),
            )
        )
