"""Tests d'intégration — le Recommendation Engine lit le diagnostic qu'il invoque.

Défaut prouvé avant correction : le moteur rendait un conseil sylvicole
complet — « éclaircie modérée, prélèvement 25 % », `niveau_confiance: 0.7` —
en citant un `diagnostic_id` tiré au hasard, jamais présent en base. La
justification portait la mention du diagnostic ; le forestier lisait une
référence vérifiable en apparence qui ne renvoyait à rien (`GSIE-CON-004`).

Deux exigences distinctes, deux tests :

* un diagnostic absent fait **refuser** — jamais produire une variante
  dégradée, qui serait un conseil sylvicole assorti d'une confiance inventée ;
* un diagnostic présent **impose sa confiance** — une recommandation ne peut
  pas être plus assurée que le diagnostic sur lequel elle repose.

Ces deux points exigent une base réelle. Les tests unitaires emploient
`SessionDiagnosticFictif`, qui rend un diagnostic pour tout identifiant :
il rend le mapping objectif → action testable sans base, mais masquerait par
construction ce qui est vérifié ici.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import create_access_token
from gsie_api.engines.recommendation.engine import (
    DiagnosticIntrouvableError,
    RecommendationEngine,
)
from gsie_api.engines.recommendation.schemas import (
    ObjectifForestier,
    RecommendationRequest,
)
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.diagnostic import DiagnosticModel
from gsie_api.infrastructure.models.enums import (
    DiagnosticGlobalState,
    DiagnosticType,
    DiagnosticValidationStatus,
    EvidenceLevel,
)
from tests.conftest import requires_docker

pytestmark = requires_docker

_TOKEN_WRITER = create_access_token(subject="test-reco-writer", claims={"roles": ["writer"]})
_HEADERS_WRITER = {"Authorization": f"Bearer {_TOKEN_WRITER}"}

# Confiance volontairement eloignee des quatre constantes que le moteur
# portait — 0,70 / 0,60 / 0,55 / 0,50. Une valeur proche laisserait le test
# passer si la correction etait annulee.
_CONFIANCE_DIAGNOSTIC = 0.33


async def _diagnostic_reel(session: AsyncSession, confiance: float) -> UUID:
    """Insère un diagnostic complet et retourne son identifiant.

    Le diagnostic hérite de `resource` (ADR-001, héritage par table de
    classe) : sa clé primaire est une clé étrangère vers `resource.id`. Créer
    la ligne fille sans sa racine échoue sur PostgreSQL — c'est précisément ce
    que SQLite laissait passer dans les tests unitaires.
    """
    identifiant = uuid4()
    session.add(
        ResourceModel(
            id=identifiant,
            type="diagnostic",
        )
    )
    await session.flush()
    session.add(
        DiagnosticModel(
            id=identifiant,
            requete_origine=uuid4(),
            station_id=uuid4(),
            type_diagnostic=DiagnosticType.stationnel,
            etat_global=DiagnosticGlobalState.sain,
            confiance=confiance,
            evidence_level_plancher=EvidenceLevel.b,
            # Seul etat qu'un moteur peut produire (`GSIE-CON-001`).
            statut_validation=DiagnosticValidationStatus.brouillon,
            date_diagnostic=datetime.now(UTC),
            # NOT NULL sans defaut serveur : l'omettre echoue a l'insertion.
            contenu={"origine": "test d'integration recommendation"},
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
async def test_un_diagnostic_absent_fait_refuser(db_session: AsyncSession) -> None:
    """Aucun conseil sylvicole sans le diagnostic qui le justifie."""
    moteur = RecommendationEngine(db_session)

    with pytest.raises(DiagnosticIntrouvableError):
        await moteur.recommend(_requete(uuid4()))


@pytest.mark.asyncio
async def test_la_confiance_vient_du_diagnostic(db_session: AsyncSession) -> None:
    """La confiance annoncée est celle du diagnostic lu, pas celle du moteur.

    Vérifie **toutes** les recommandations de l'ensemble, principale et
    alternatives : le moteur portait une constante différente par générateur,
    et ne contrôler que la principale laisserait trois constantes en place.
    """
    identifiant = await _diagnostic_reel(db_session, _CONFIANCE_DIAGNOSTIC)

    ensemble = await RecommendationEngine(db_session).recommend(_requete(identifiant))

    # Les alternatives sont imbriquees sous chaque recommandation. Ne verifier
    # que `ensemble.recommandations` laisserait passer trois des quatre
    # constantes que le moteur portait : elles vivaient dans les generateurs
    # d'alternatives.
    toutes = [
        candidate for reco in ensemble.recommandations for candidate in (reco, *reco.alternatives)
    ]
    assert len(toutes) > 1, (
        "l'ensemble ne porte aucune alternative : le test ne couvrirait alors "
        "que le generateur principal"
    )

    fautives = [
        (candidate.type_action, candidate.niveau_confiance)
        for candidate in toutes
        if candidate.niveau_confiance != pytest.approx(_CONFIANCE_DIAGNOSTIC)
    ]
    assert not fautives, (
        f"confiance(s) ne provenant pas du diagnostic : {fautives}. Attendu "
        f"{_CONFIANCE_DIAGNOSTIC} partout — une recommandation ne peut pas être "
        "plus assurée que le diagnostic qui la fonde."
    )


# --- Meme exigence, vue depuis l'API HTTP ------------------------------------


@pytest.fixture
async def client_recommendation(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP sur une app minimale n'incluant que le routeur recommendation."""
    from gsie_api.engines.recommendation.router import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_l_api_refuse_un_diagnostic_absent(
    client_recommendation: AsyncClient,
) -> None:
    """Le refus remonte en 4xx explicite, jamais en 200 ni en 500.

    Un 500 dirait « panne du serveur » là où le refus est un jugement du
    moteur ; un 200 rendrait le conseil. Le corps doit nommer le diagnostic
    manquant, sans quoi l'appelant ne peut pas corriger sa requête.
    """
    diagnostic_absent = uuid4()

    reponse = await client_recommendation.post(
        "/recommendation/recommend",
        json=_requete(diagnostic_absent).model_dump(mode="json"),
        headers=_HEADERS_WRITER,
    )

    assert 400 <= reponse.status_code < 500, (
        f"statut {reponse.status_code} — attendu un refus explicite. "
        f"Corps : {reponse.text[:300]}"
    )
    assert str(diagnostic_absent) in reponse.text, (
        "le refus ne nomme pas le diagnostic manquant : l'appelant ne peut "
        f"pas corriger. Corps : {reponse.text[:300]}"
    )
