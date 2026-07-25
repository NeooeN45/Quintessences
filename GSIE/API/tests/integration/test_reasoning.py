"""Tests d'intégration — Reasoning Engine (API HTTP, inférence explicable).

Couvre : appel nominal (200 + InferenceResult valide), requête sans
contexte (422), authentification insuffisante (401 sans token, 403 rôle
lecteur sur mutation), sérialisation JSON round-trip sans perte.

Utilise httpx.AsyncClient (ASGITransport) avec la session DB de test
(testcontainers), branchée sur une app FastAPI minimale n'incluant que
le routeur reasoning — l'app principale n'inclut pas encore ce routeur
(app.py sera mis à jour par l'agent responsable de l'assemblage).

Dépendance : gsie_api.engines.reasoning.engine (implémenté par l'agent R2
en parallèle). Si ce module n'est pas disponible, les tests échouent à
la collection — c'est le signal attendu de la dépendance, pas une
désactivation.
"""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.auth import create_access_token
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    ReasoningRequest,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.infrastructure.database import get_db
from tests.conftest import requires_docker

pytestmark = requires_docker

# --- Tokens JWT pour les tests RBAC ---
_TOKEN_WRITER = create_access_token(subject="test-reasoning-writer", claims={"roles": ["writer"]})
_TOKEN_READER = create_access_token(subject="test-reasoning-reader", claims={"roles": ["reader"]})
_HEADERS_WRITER = {"Authorization": f"Bearer {_TOKEN_WRITER}"}
_HEADERS_READER = {"Authorization": f"Bearer {_TOKEN_READER}"}


def _make_source() -> SourceReference:
    """Source réaliste — Référentiel pédologique français (INRAE 2008)."""
    return SourceReference(
        type_source=SourceType.referentiel_officiel,
        auteur="INRAE (2008)",
        date_publication="2008",
        reference="Référentiel pédologique français, édition 2008",
    )


def _make_bloc_pedologie() -> BlocContexte:
    """Bloc de contexte pédologique — station acide typique."""
    return BlocContexte(
        source_moteur=SourceMoteurContexte.pedology,
        source=_make_source(),
        evidence_level=EvidenceLevel.B,
        valeurs={"pH": 5.2, "profondeur_cm": 80, "texture": "sablonneux"},
    )


def _make_request(
    question: str = "Quelles essences sont adaptées à cette station ?",
    profondeur_max: int = 5,
) -> ReasoningRequest:
    """Construit une ReasoningRequest valide pour les tests."""
    return ReasoningRequest(
        requete_id=uuid4(),
        station_id=uuid4(),
        contexte=StationContexte(pedologie=_make_bloc_pedologie()),
        question=question,
        profondeur_max=profondeur_max,
    )


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient branché sur une app minimale n'incluant que le routeur reasoning.

    L'app principale (create_app) n'inclut pas encore le routeur reasoning
    — l'enregistrement dans app.py est du ressort de l'agent d'assemblage.
    En attendant, les tests montent leur propre app avec dependency override
    de get_db sur la session de test (même pattern que test_pipeline_api.py).
    """
    from gsie_api.engines.reasoning.router import router as reasoning_router

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = FastAPI()
    app.include_router(reasoning_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Tests : appel nominal ---


async def should_return_200_with_valid_inference_result(client: AsyncClient):
    """Un appel nominal avec contexte valide retourne 200 et un InferenceResult."""
    request = _make_request()
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=request.model_dump(mode="json"),
        headers=_HEADERS_WRITER,
    )
    assert response.status_code == 200
    data = response.json()
    assert "resultat_id" in data
    assert "requete_origine" in data
    assert "conclusions" in data
    assert "contradictions" in data
    assert "date_inference" in data
    assert data["requete_origine"] == str(request.requete_id)


async def should_serialize_and_deserialize_inference_result_without_loss(
    client: AsyncClient,
):
    """La réponse JSON se désérialise en InferenceResult sans perte."""
    from gsie_api.engines.reasoning.schemas import InferenceResult

    request = _make_request()
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=request.model_dump(mode="json"),
        headers=_HEADERS_WRITER,
    )
    assert response.status_code == 200
    raw_json = response.json()

    # Désérialisation : la réponse doit être un InferenceResult valide
    result = InferenceResult.model_validate(raw_json)

    # Re-sérialisation : pas de perte (round-trip stable)
    re_serialized = result.model_dump(mode="json")
    assert re_serialized == raw_json


# --- Tests : validation 422 ---


async def should_return_422_when_contexte_missing(client: AsyncClient):
    """Une requête sans le champ contexte retourne 422."""
    payload = {
        "requete_id": str(uuid4()),
        "question": "Quelles essences sont adaptées ?",
        "profondeur_max": 5,
    }
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=payload,
        headers=_HEADERS_WRITER,
    )
    assert response.status_code == 422


async def should_return_422_when_contexte_empty(client: AsyncClient):
    """Un contexte stationnel vide (aucun bloc) retourne 422."""
    payload = {
        "requete_id": str(uuid4()),
        "contexte": {
            "geographie": None,
            "climat": None,
            "pedologie": None,
            "botanique": None,
            "peuplement": None,
            "correlations": [],
        },
        "question": "Quelles essences sont adaptées ?",
        "profondeur_max": 5,
    }
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=payload,
        headers=_HEADERS_WRITER,
    )
    assert response.status_code == 422


# --- Tests : authentification et RBAC ---


async def should_return_401_when_infer_without_auth_token(client: AsyncClient):
    """POST /reasoning/infer sans token JWT retourne 401 (authentification requise)."""
    request = _make_request()
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=request.model_dump(mode="json"),
    )
    assert response.status_code == 401


async def should_return_403_when_reader_attempts_mutation(client: AsyncClient):
    """POST /reasoning/infer avec un rôle lecteur retourne 403 (mutation requiert writer)."""
    request = _make_request()
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=request.model_dump(mode="json"),
        headers=_HEADERS_READER,
    )
    assert response.status_code == 403


# --- Tests : endpoints publics (status, version) ---


async def should_return_200_for_status_without_auth(client: AsyncClient):
    """GET /reasoning/status est public — aucun token requis."""
    response = await client.get("/api/v1/reasoning/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "reasoning"
    assert data["status"] == "active"


async def should_return_200_for_version_without_auth(client: AsyncClient):
    """GET /reasoning/version est public — aucun token requis."""
    response = await client.get("/api/v1/reasoning/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "backend" in data


# --- Tests : réponse d'erreur ne divulgue pas d'information interne ---


async def should_not_leak_internal_details_in_error_response(client: AsyncClient):
    """Une erreur 422 ne doit divulguer ni chemin de fichier, ni trace, ni structure interne."""
    payload = {
        "requete_id": str(uuid4()),
        "question": "Quelles essences ?",
        "profondeur_max": 5,
    }
    response = await client.post(
        "/api/v1/reasoning/infer",
        json=payload,
        headers=_HEADERS_WRITER,
    )
    assert response.status_code == 422
    body = response.text
    # Aucun chemin de fichier Windows ou Unix, ni traceback Python
    assert ".py" not in body
    assert "Traceback" not in body
    assert "File " not in body
