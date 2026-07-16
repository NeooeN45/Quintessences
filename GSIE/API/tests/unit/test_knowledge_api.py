"""Tests API — endpoints du Knowledge Engine (legacy v6.1).

Teste les endpoints FastAPI : /knowledge/status, /version, /ingest, /query, /revise, /stats.

NOTE : Ces tests référencent l'ancien schéma v6.1. La migration v6.2
(RFC-0012) remplace KnowledgeObject par Assertion. Les endpoints
/knowledge/* seront migrés vers le CRUD générique /resources en Vague 2.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.engines.evidence.schemas import (
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
    SourceType,
)
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    DomaineValidite,
    KnowledgeIngestRequest,
    KnowledgeQuery,
    KnowledgeType,
    QueryType,
)

pytestmark = pytest.mark.skip(
    reason="Schéma v6.1 legacy — migration v6.2 (RFC-0012) remplace KnowledgeObject par Assertion"
)

app = create_app()
client = TestClient(app)

_ACCESS_TOKEN = create_access_token(subject="test-knowledge")
_AUTH_HEADERS = {"Authorization": f"Bearer {_ACCESS_TOKEN}"}


@pytest.fixture(autouse=True)
def _reset_engine():
    """Réinitialise le singleton KnowledgeEngine avant chaque test (isolation)."""
    from gsie_api.engines.knowledge.router import _engine

    _engine._store.clear()
    yield
    _engine._store.clear()


def _make_ingest_payload(
    type_: KnowledgeType = KnowledgeType.concept,
    titre: str = "Autécologie du chêne sessile",
    evidence_level: EvidenceLevel = EvidenceLevel.B,
    statut: KnowledgeStatus = KnowledgeStatus.accepte,
) -> dict[str, object]:
    """Crée un payload d'ingestion valide pour les tests API."""
    req = KnowledgeIngestRequest(
        connaissance_id=uuid4(),
        contenu_normalise={"definition": "Test connaissance", "data": 42},
        type=type_,
        titre=titre,
        description="Description de test pour le Knowledge Engine.",
        domaine_scientifique=DomaineScientifique.ecologie_forestiere,
        evidence_level=evidence_level,
        source=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="Flore forestière française, tome 1, IDF",
        ),
        statut=statut,
        domaines_validite=[
            DomaineValidite(parametre="pH", minimum=4.5, maximum=6.5, unite="unité pH"),
        ],
        moteurs_consommateurs=["Pedology", "Diagnostic"],
        mots_cles=["chêne sessile", "pH", "seuil"],
    )
    return req.model_dump(mode="json")


# --- Tests status et version ---


def should_return_200_when_knowledge_status_requested():
    """GET /api/v1/knowledge/status doit retourner 200."""
    response = client.get("/api/v1/knowledge/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "knowledge"
    assert data["status"] == "active"


def should_return_200_when_knowledge_version_requested():
    """GET /api/v1/knowledge/version doit retourner la version."""
    response = client.get("/api/v1/knowledge/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "backend" in data


# --- Tests ingest ---


def should_return_201_when_valid_knowledge_ingested():
    """POST /api/v1/knowledge/ingest doit retourner 201 avec le KnowledgeObject."""
    payload = _make_ingest_payload()
    response = client.post(
        "/api/v1/knowledge/ingest",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["version"] == 1
    assert data["type"] == "concept"
    assert data["historique"] == []


def should_return_400_when_ingesting_refused_knowledge():
    """POST /api/v1/knowledge/ingest doit retourner 400 si statut=refuse."""
    payload = _make_ingest_payload(statut=KnowledgeStatus.refuse)
    response = client.post(
        "/api/v1/knowledge/ingest",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 400


def should_return_400_when_ingesting_quarantine_knowledge():
    """POST /api/v1/knowledge/ingest doit retourner 400 si statut=quarantine."""
    payload = _make_ingest_payload(statut=KnowledgeStatus.quarantine)
    response = client.post(
        "/api/v1/knowledge/ingest",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 400


def should_return_422_when_ingest_missing_titre():
    """POST /api/v1/knowledge/ingest doit retourner 422 si titre manquant."""
    payload = _make_ingest_payload()
    payload["titre"] = ""
    response = client.post(
        "/api/v1/knowledge/ingest",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 422


# --- Tests query ---


def should_return_200_when_querying_empty_graph():
    """POST /api/v1/knowledge/query doit retourner 200 sur graphe vide."""
    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    response = client.post(
        "/api/v1/knowledge/query",
        json=query.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["connaissances"] == []


def should_return_knowledge_when_querying_after_ingest():
    """POST /api/v1/knowledge/query doit retourner les connaissances ingérées."""
    # Ingest
    payload = _make_ingest_payload(type_=KnowledgeType.concept)
    client.post("/api/v1/knowledge/ingest", json=payload, headers=_AUTH_HEADERS)

    # Query
    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    response = client.post(
        "/api/v1/knowledge/query",
        json=query.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["connaissances"]) >= 1


# --- Tests revise ---


def should_return_200_when_revising_existing_knowledge():
    """POST /api/v1/knowledge/revise doit retourner 200 avec la nouvelle version."""
    # Ingest d'abord
    payload = _make_ingest_payload()
    ingest_response = client.post(
        "/api/v1/knowledge/ingest",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_response.status_code == 201
    connaissance_id = payload["connaissance_id"]

    # Réviser
    revision = {
        "connaissance_id": str(connaissance_id),
        "justification": "Nouvelle publication 2028 invalide le seuil",
        "nouveau_contenu": {"parametre": "pH", "minimum": 4.0, "maximum": 6.0},
    }
    response = client.post(
        "/api/v1/knowledge/revise",
        json=revision,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 2
    assert len(data["historique"]) == 1


def should_return_404_when_revising_unknown_knowledge():
    """POST /api/v1/knowledge/revise doit retourner 404 si UUID inexistant."""
    revision = {
        "connaissance_id": str(uuid4()),
        "justification": "Test",
        "nouveau_contenu": {"test": True},
    }
    response = client.post(
        "/api/v1/knowledge/revise",
        json=revision,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 404


def should_return_400_when_revising_without_changes():
    """POST /api/v1/knowledge/revise doit retourner 400 si aucun champ modifié."""
    # Ingest d'abord
    payload = _make_ingest_payload()
    client.post("/api/v1/knowledge/ingest", json=payload, headers=_AUTH_HEADERS)

    # Réviser sans changement
    revision = {
        "connaissance_id": str(payload["connaissance_id"]),
        "justification": "Test sans changement",
    }
    response = client.post(
        "/api/v1/knowledge/revise",
        json=revision,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 400


# --- Tests stats ---


def should_return_200_when_stats_requested():
    """GET /api/v1/knowledge/stats doit retourner 200 avec les statistiques."""
    response = client.get(
        "/api/v1/knowledge/stats",
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_objects" in data


# --- Tests d'authentification ---


def should_return_401_when_ingest_without_auth():
    """POST /api/v1/knowledge/ingest sans auth doit retourner 401."""
    payload = _make_ingest_payload()
    response = client.post("/api/v1/knowledge/ingest", json=payload)
    assert response.status_code == 401


def should_return_401_when_query_without_auth():
    """POST /api/v1/knowledge/query sans auth doit retourner 401."""
    query = KnowledgeQuery(requete_id=uuid4(), type=QueryType.par_concept)
    response = client.post("/api/v1/knowledge/query", json=query.model_dump(mode="json"))
    assert response.status_code == 401
