"""Tests E2E — pipeline Evidence → Knowledge via l'API HTTP (async).

Contrairement à tests/integration/test_pipeline.py (niveau moteur, sans
HTTP), ceux-ci passent par les endpoints /api/v1/evidence et
/api/v1/knowledge via httpx.AsyncClient (ASGITransport), avec la session
DB de test (testcontainers) branchée sur l'app FastAPI via dependency
override de get_db — sinon l'app utiliserait sa propre connexion (non
configurée en test).

Note : TestClient (synchrone) a été abandonné ici car il exécute les
requêtes sur une boucle asyncio différente de celle où pytest-asyncio
crée la fixture db_session, ce qui casse dès qu'une requête écrit
réellement en base ('attached to a different loop'). httpx.AsyncClient
partage la boucle du test et n'a pas ce problème.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.engines.evidence.schemas import (
    ContentType,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.infrastructure.database import get_db
from tests.conftest import requires_docker

pytestmark = requires_docker

_ACCESS_TOKEN = create_access_token(subject="test-pipeline")
_AUTH_HEADERS = {"Authorization": f"Bearer {_ACCESS_TOKEN}"}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient dont la dépendance get_db est branchée sur la session de test."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


async def should_complete_full_pipeline_via_api(client: AsyncClient):
    """Le pipeline complet doit fonctionner via les endpoints API."""
    sub = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.publication,
        contenu={"definition": "RUM du hêtre", "minimum": 80},
        source_candidate=SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Rameau et al. (2008)",
            date_publication="2008",
            reference="Flore forestière française, tome 1, IDF",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_e2e",
    )
    evidence_resp = await client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    assert evidence_resp.status_code == 200
    evidence_data = evidence_resp.json()
    assert evidence_data["statut"] == "accepte"
    assert evidence_data["evidence_level"] == "B"

    ingest_payload = {
        "connaissance_id": evidence_data["connaissance_id"],
        "contenu_normalise": evidence_data["contenu_normalise"],
        "type": "concept",
        "titre": "RUM du hêtre",
        "description": "Réserve utile en eau minimale pour le hêtre (80 mm).",
        "domaine_scientifique": "pedologie",
        "evidence_level": evidence_data["evidence_level"],
        "source": evidence_data["source"],
        "statut": evidence_data["statut"],
        "mots_cles": ["hêtre", "RUM", "eau"],
    }
    ingest_resp = await client.post(
        "/api/v1/knowledge/ingest",
        json=ingest_payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_resp.status_code == 201
    ingest_data = ingest_resp.json()
    assert ingest_data["version"] == 1

    query_payload = {
        "requete_id": str(uuid4()),
        "type": "par_concept",
    }
    query_resp = await client.post(
        "/api/v1/knowledge/query",
        json=query_payload,
        headers=_AUTH_HEADERS,
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total"] >= 1
    found = [k for k in query_data["connaissances"] if k["titre"] == "RUM du hêtre"]
    assert len(found) == 1
    assert found[0]["evidence_level"] == "B"


async def should_complete_full_pipeline_with_revision_via_api(client: AsyncClient):
    """Pipeline complet avec révision : evaluate → ingest → revise → query v2."""
    sub = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.referentiel,
        contenu={"parametre": "pH", "minimum": 4.5, "maximum": 6.5},
        source_candidate=SourceReference(
            type_source=SourceType.referentiel_officiel,
            auteur="INRAE (2008)",
            reference="Référentiel pédologique français",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_e2e_revision",
    )
    evidence_resp = await client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    evidence_data = evidence_resp.json()

    ingest_payload = {
        "connaissance_id": evidence_data["connaissance_id"],
        "contenu_normalise": evidence_data["contenu_normalise"],
        "type": "seuil",
        "titre": "pH optimal chêne sessile",
        "description": "pH 4,5-6,5 pour le chêne sessile.",
        "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        "evidence_level": evidence_data["evidence_level"],
        "source": evidence_data["source"],
        "statut": evidence_data["statut"],
    }
    ingest_resp = await client.post(
        "/api/v1/knowledge/ingest",
        json=ingest_payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_resp.status_code == 201
    connaissance_id = ingest_resp.json()["connaissance_id"]

    revision_payload = {
        "connaissance_id": str(connaissance_id),
        "justification": "Nouvelle étude 2028 élargit la gamme à 4,0-7,0",
        "nouveau_contenu": {"parametre": "pH", "minimum": 4.0, "maximum": 7.0},
    }
    revise_resp = await client.post(
        "/api/v1/knowledge/revise",
        json=revision_payload,
        headers=_AUTH_HEADERS,
    )
    assert revise_resp.status_code == 200
    revised_data = revise_resp.json()
    assert revised_data["version"] == 2
    assert len(revised_data["historique"]) == 1
    assert revised_data["historique"][0]["version"] == 1

    query_payload = {
        "requete_id": str(uuid4()),
        "type": "par_domaine",
        "filtres": {
            "connaissance_id": str(connaissance_id),
            "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        },
    }
    query_resp = await client.post(
        "/api/v1/knowledge/query",
        json=query_payload,
        headers=_AUTH_HEADERS,
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total"] == 1
    assert query_data["connaissances"][0]["version"] == 2
    assert query_data["connaissances"][0]["contenu"]["minimum"] == 4.0


async def should_not_ingest_refused_knowledge_via_api(client: AsyncClient):
    """Une connaissance refusée par Evidence ne doit pas être ingérée."""
    sub = RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.observation,
        contenu={"observation": "Test"},
        source_candidate=SourceReference(
            type_source=SourceType.observation_terrain,
            auteur="Observateur test",
            reference="Obs-2026-001",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_e2e_refuse",
    )
    evidence_resp = await client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    evidence_data = evidence_resp.json()
    assert evidence_data["statut"] == "refuse"

    ingest_payload = {
        "connaissance_id": evidence_data["connaissance_id"],
        "contenu_normalise": evidence_data["contenu_normalise"],
        "type": "concept",
        "titre": "Test refuse",
        "description": "Description test.",
        "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
        "evidence_level": evidence_data["evidence_level"],
        "source": evidence_data["source"],
        "statut": evidence_data["statut"],
    }
    ingest_resp = await client.post(
        "/api/v1/knowledge/ingest",
        json=ingest_payload,
        headers=_AUTH_HEADERS,
    )
    assert ingest_resp.status_code == 400
