"""Tests d'intégration — la chaîne complète en un appel HTTP.

    POST /api/v1/orchestration/analyse

Ce que l'endpoint résout : aucun endpoint ne couvrait la chaîne, et les
conversions entre moteurs vivaient dans `validation_pipeline.py` sans être
exposées. Un client — l'application GeoSylva — devait enchaîner quatre appels
et reproduire ces conversions de son côté.

Ce que ces tests éprouvent, et qui est l'essentiel : l'orchestration **ne
décide de rien**. Elle refuse plutôt que de combler un manque par une valeur
par défaut. Classer une conclusion d'office reviendrait à décider à la place du
forestier, et le conseil sylvicole qui en découlerait porterait une chaîne
complète — invisible (`GSIE-CON-001`, `ADR-009`).
"""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import create_access_token
from gsie_api.infrastructure.database import get_db
from tests.conftest import requires_docker

pytestmark = requires_docker

_TOKEN = create_access_token(subject="test-orchestration", claims={"roles": ["writer"]})
_HEADERS = {"Authorization": f"Bearer {_TOKEN}"}

_SOURCE = {
    "type_source": "referentiel_officiel",
    "auteur": "INRAE (2008)",
    "date_publication": "2008",
    "reference": "Référentiel pédologique français, édition 2008",
}


def _corps(
    *,
    avec_qualification_profondeur: bool = True,
    ph: float = 5.2,
) -> dict:
    """Requête complète, station acide et profonde — deux règles concluent.

    `avec_qualification_profondeur=False` retire une qualification tout en
    laissant sa règle conclure : c'est le cas que l'orchestration doit refuser.
    """
    qualifications = [
        {
            "identifiant_regle": "regle-acidite-01",
            "role": "contrainte",
            "domaine_element": "pedologique",
        }
    ]
    if avec_qualification_profondeur:
        qualifications.append(
            {
                "identifiant_regle": "regle-profondeur-01",
                "role": "atout",
                "domaine_element": "pedologique",
            }
        )

    return {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": _SOURCE,
                "evidence_level": "B",
                "valeurs": {"pH": ph, "profondeur_cm": 80},
            }
        },
        "regles": [
            {
                "identifiant": "regle-acidite-01",
                "condition": "pedologie_pH < 5.5",
                "enonce_conclusion": "Le sol est acide.",
                "source": _SOURCE,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            },
            {
                "identifiant": "regle-profondeur-01",
                "condition": "pedologie_profondeur_cm > 50",
                "enonce_conclusion": "Le sol est profond.",
                "source": _SOURCE,
                "evidence_level": "B",
                "niveau_confiance": 0.80,
            },
        ],
        "qualifications": qualifications,
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": "Acidité marquée constatée sur la station",
            "source": _SOURCE,
            "evidence_level": "B",
        },
        "question": "Quelles essences sont adaptées à cette station ?",
        "objectif_forestier": "production",
        "alternatives_demandees": True,
    }


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client sur l'application réelle, session de test injectée."""
    from gsie_api.engines.orchestration.router import router

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_un_appel_deroule_la_chaine_entiere(client: AsyncClient) -> None:
    """Les quatre sorties reviennent dans une seule réponse.

    Les quatre, et pas seulement la dernière : un forestier à qui l'on
    présenterait la seule recommandation ne pourrait voir ni le raisonnement qui
    la fonde, ni le diagnostic qu'elle invoque, ni ce que la validation a
    contrôlé (`GSIE-CON-004`).
    """
    reponse = await client.post("/api/v1/orchestration/analyse", json=_corps(), headers=_HEADERS)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()

    assert len(corps["inference"]["conclusions"]) == 2
    assert corps["diagnostic"]["etat_global"] == "vigueur_reduite"
    assert corps["recommandations"]["recommandations"], "aucune recommandation produite"
    assert corps["validation"]["statut"] != "bloque", (
        f"la chaîne est bloquée par sa propre validation : "
        f"{corps['validation']['causes_blocage']}"
    )


@pytest.mark.asyncio
async def test_la_recommandation_se_rattache_au_diagnostic_produit(
    client: AsyncClient,
) -> None:
    """Le chaînage est réel, pas juxtaposé.

    Sans ce contrôle, une orchestration qui appellerait les quatre moteurs sur
    des entrées indépendantes rendrait quatre sorties cohérentes en apparence et
    sans lien entre elles.
    """
    corps = (
        await client.post("/api/v1/orchestration/analyse", json=_corps(), headers=_HEADERS)
    ).json()

    assert (
        corps["recommandations"]["diagnostic_source"] == corps["diagnostic"]["diagnostic_id"]
    ), "les recommandations ne se rattachent pas au diagnostic de la même analyse"

    conclusions = {c["conclusion_id"] for c in corps["inference"]["conclusions"]}
    assert (
        set(corps["diagnostic"]["conclusions_source"]) == conclusions
    ), "le diagnostic ne cite pas les conclusions produites par ce même appel"


@pytest.mark.asyncio
async def test_une_conclusion_sans_qualification_fait_refuser(client: AsyncClient) -> None:
    """L'orchestration ne classe pas une conclusion à la place du forestier.

    La règle `regle-profondeur-01` conclut, mais sa qualification n'est pas
    déclarée. Attribuer un rôle par défaut produirait un diagnostic complet dont
    un élément serait classé par la machine — et le conseil sylvicole qui en
    découle citerait une chaîne entière, sans que rien ne signale l'invention.

    Le refus nomme la **règle**, que l'appelant connaît, et non l'identifiant de
    conclusion qu'il n'a jamais vu.
    """
    reponse = await client.post(
        "/api/v1/orchestration/analyse",
        json=_corps(avec_qualification_profondeur=False),
        headers=_HEADERS,
    )

    assert reponse.status_code == 400, reponse.text
    assert (
        "regle-profondeur-01" in reponse.text
    ), f"le refus ne nomme pas la règle non qualifiée : {reponse.text[:300]}"


@pytest.mark.asyncio
async def test_aucune_regle_applicable_fait_refuser_avec_son_motif(
    client: AsyncClient,
) -> None:
    """Un raisonnement sans conclusion ne produit pas un diagnostic vide.

    Le pH est porté au-dessus du seuil : la règle d'acidité ne s'applique plus.
    Rendre 200 avec un diagnostic vide laisserait l'appelant interpréter le
    silence, alors que « aucune règle ne s'applique » est une réponse.
    """
    corps = _corps(ph=7.0)
    corps["regles"] = [corps["regles"][0]]
    corps["qualifications"] = [corps["qualifications"][0]]

    reponse = await client.post("/api/v1/orchestration/analyse", json=corps, headers=_HEADERS)

    assert reponse.status_code == 400, reponse.text
    assert (
        "aucune conclusion" in reponse.text.lower()
    ), f"le refus n'explique pas pourquoi : {reponse.text[:300]}"
