"""Tests E2E — API GSIE via TestClient FastAPI (bout en bout).

Couvre les endpoints de bout en bout : middleware -> auth -> router ->
service -> engine -> response. Trois categories :

A. Endpoints sans DB (status, version, health, ready, auth 404) — pas de Docker.
B. Endpoints avec DB (correlation compute, resources CRUD, pipeline) — Docker requis.
C. Chaine cross-moteurs (correlation -> reasoning -> diagnostic) — Docker requis.

Les tests B et C sont marqués `requires_docker` et skip si Docker indisponible.
Les tests A tournent partout (CI sans Docker, machine de dev).

Note : les tests DB utilisent httpx.AsyncClient (pas TestClient synchrone) car
asyncpg casse sur une boucle asyncio différente — voir test_pipeline_api.py.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
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

# Token JWT de test — roles writer pour les endpoints POST
_TEST_TOKEN = create_access_token(subject="test-e2e", claims={"roles": ["writer"]})
_AUTH_HEADERS = {"Authorization": f"Bearer {_TEST_TOKEN}"}
_READ_TOKEN = create_access_token(subject="test-e2e-read", claims={"roles": ["reader"]})
_READ_HEADERS = {"Authorization": f"Bearer {_READ_TOKEN}"}


# ---------------------------------------------------------------------------
# A. Endpoints sans DB — tournent partout
# ---------------------------------------------------------------------------


class TestHealthAndReady:
    """Health et ready endpoints — pas de DB requise."""

    def should_return_200_on_health(self) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def should_return_200_on_ready(self) -> None:
        """GET /ready — le code HTTP suit l'état réel des dépendances.

        Ce test exigeait `200` inconditionnellement, et passait parce que
        l'endpoint rendait `200` quel que soit l'état : il ne pouvait pas
        échouer sur cet axe. L'environnement de test n'a pas toujours Redis, et
        un `degraded` doit précisément se voir.

        L'invariant contrôlé est la cohérence code ↔ corps : c'est lui qui a de
        la valeur pour une sonde Kubernetes, et il tient que les dépendances
        soient là ou non.
        """
        app = create_app()
        client = TestClient(app)
        response = client.get("/ready")

        corps = response.json()
        attendu = 200 if corps["status"] == "healthy" else 503
        assert response.status_code == attendu, (
            f"HTTP {response.status_code} pour un corps {corps['status']!r} — "
            f"une sonde de disponibilité décide sur le code. {corps['dependencies']}"
        )


class TestEngineStatusEndpoints:
    """Endpoints /status de chaque moteur — pas de DB, juste un retour statique."""

    @pytest.mark.parametrize(
        "engine",
        [
            "evidence",
            "knowledge",
            "correlation",
            "reasoning",
            "diagnostic",
            "gis",
            "climate",
            "pedology",
        ],
    )
    def should_return_200_on_engine_status(self, engine: str) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.get(f"/api/v1/{engine}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["engine"] == engine
        assert "status" in data

    @pytest.mark.parametrize(
        "engine",
        ["correlation", "reasoning", "diagnostic"],
    )
    def should_return_version_on_engine_version(self, engine: str) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.get(f"/api/v1/{engine}/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "backend" in data


class TestAuthGate:
    """L'auth JWT doit bloquer les endpoints proteges sans token."""

    def should_return_401_when_no_token_on_correlation_compute(self) -> None:
        app = create_app()
        client = TestClient(app)
        # Payload minimal invalide — on veut juste tester le gate auth
        response = client.post(
            "/api/v1/correlation/compute",
            json={"requete_id": str(uuid4()), "domaine": "stationnel"},
        )
        assert response.status_code == 401

    def should_return_401_when_no_token_on_resources(self) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/resources")
        assert response.status_code == 401

    def should_return_401_when_invalid_token(self) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/resources",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def should_return_404_on_login_when_dev_disabled(self) -> None:
        """Le login doit retourner 404 quand dev login est desactive."""
        with patch("gsie_api.auth.router._settings") as mock_settings:
            mock_settings.auth_dev_login_enabled = False
            mock_settings.auth_dev_username = None
            mock_settings.auth_dev_password = None
            app = create_app()
            client = TestClient(app)
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "admin"},
            )
            assert response.status_code == 404


class TestOpenAPI:
    """OpenAPI spec doit etre servie en dev."""

    def should_return_200_on_openapi(self) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "GSIE API"
        # Tous les moteurs doivent apparaitre dans les paths
        paths = data["paths"]
        assert "/api/v1/correlation/compute" in paths
        assert "/api/v1/reasoning/infer" in paths
        assert "/api/v1/diagnostic/diagnostiquer" in paths


# ---------------------------------------------------------------------------
# B. Endpoints avec DB — Docker requis
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient dont la dépendance get_db est branchée sur la session de test.

    On utilise httpx.AsyncClient (pas TestClient synchrone) car asyncpg casse
    sur une boucle asyncio différente — voir test_pipeline_api.py.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@requires_docker
class TestCorrelationComputeE2E:
    """POST /correlation/compute — calcul reel avec persistance."""

    async def should_compute_and_persist_correlation(self, async_client: AsyncClient) -> None:
        payload = {
            "requete_id": str(uuid4()),
            "domaine": "stationnel",
            "variable_a": {
                "source_moteur": "PEDOLOGY",
                "variable": "pH",
                "valeurs": [4.0, 4.5, 5.0, 5.5, 6.0],
            },
            "variable_b": {
                "source_moteur": "BOTANICAL",
                "variable": "presence_chene_sessile",
                "valeurs": [0.1, 0.3, 0.5, 0.7, 0.9],
            },
            "methode": "pearson",
            "seuil_significativite": 0.05,
            "source": {
                "type_source": "referentiel_officiel",
                "auteur": "Rameau et al. (2008)",
                "reference": "Flore forestiere francaise, tome 1, IDF",
            },
            "evidence_level": "B",
            "domaine_validite": "France atlantique, sols acides",
        }
        response = await async_client.post(
            "/api/v1/correlation/compute",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["coefficient"] == pytest.approx(1.0, abs=1e-6)
        assert data["type_relation"] == "positive"
        assert data["n_observations"] == 5
        assert data["methode"] == "pearson"
        # ADR-009 : la source doit etre preservee
        assert data["source"]["auteur"] == "Rameau et al. (2008)"
        assert data["evidence_level"] == "B"

    async def should_return_400_when_method_not_calculable(self, async_client: AsyncClient) -> None:
        payload = {
            "requete_id": str(uuid4()),
            "domaine": "stationnel",
            "variable_a": {
                "source_moteur": "PEDOLOGY",
                "variable": "pH",
                "valeurs": [4.0, 4.5, 5.0],
            },
            "variable_b": {
                "source_moteur": "BOTANICAL",
                "variable": "presence",
                "valeurs": [0.1, 0.3, 0.5],
            },
            "methode": "expert",  # non calculable
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
        }
        response = await async_client.post(
            "/api/v1/correlation/compute",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 400

    async def should_return_422_when_valeurs_not_appariees(self, async_client: AsyncClient) -> None:
        payload = {
            "requete_id": str(uuid4()),
            "domaine": "stationnel",
            "variable_a": {
                "source_moteur": "PEDOLOGY",
                "variable": "pH",
                "valeurs": [4.0, 4.5, 5.0, 5.5],
            },
            "variable_b": {
                "source_moteur": "BOTANICAL",
                "variable": "presence",
                "valeurs": [0.1, 0.3, 0.5],  # longueur differente
            },
            "methode": "pearson",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
        }
        response = await async_client.post(
            "/api/v1/correlation/compute",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 422


@requires_docker
class TestPipelineE2E:
    """Chaine Evidence -> Knowledge via API (deja couvert par test_pipeline_api,
    on ajoute ici un test de bout en bout avec verification ADR-009)."""

    async def should_evaluate_and_preserve_evidence_level(self, async_client: AsyncClient) -> None:
        """ADR-009 : le niveau de preuve doit etre preserve dans la reponse."""
        sub = RawKnowledgeSubmission(
            soumission_id=uuid4(),
            type_contenu=ContentType.publication,
            contenu={"definition": "RUM du hetre", "minimum": 80},
            source_candidate=SourceReference(
                type_source=SourceType.peer_reviewed,
                auteur="Rameau et al. (2008)",
                date_publication="2008",
                reference="Flore forestiere francaise, tome 1, IDF",
            ),
            date_soumission=datetime.now(UTC),
            soumetteur="test_e2e",
        )
        response = await async_client.post(
            "/api/v1/evidence/evaluate",
            json=sub.model_dump(mode="json"),
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        # peer_reviewed + publication -> niveau B
        assert data["evidence_level"] == "B"
        assert data["statut"] == "accepte"
        # ADR-009 : la source doit etre preservee
        assert data["source"]["auteur"] == "Rameau et al. (2008)"


@requires_docker
class TestReasoningE2E:
    """POST /reasoning/infer — inférence avec contexte stationnel."""

    async def should_return_empty_conclusions_when_no_regles(
        self, async_client: AsyncClient
    ) -> None:
        """Sans regles, le moteur doit retourner un resultat honnete (vide)."""
        payload = {
            "requete_id": str(uuid4()),
            "contexte": {
                "pedologie": {
                    "source_moteur": "PEDOLOGY",
                    "source": {
                        "type_source": "referentiel_officiel",
                        "auteur": "IGN",
                        "reference": "Sol de test",
                    },
                    "evidence_level": "B",
                    "valeurs": {"pH": 4.5},
                }
            },
            "regles": [],
            "question": "Quelle essence adapter?",
            "profondeur_max": 5,
        }
        response = await async_client.post(
            "/api/v1/reasoning/infer",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        # Sans regles, pas de conclusions — resultat honnete
        assert data["conclusions"] == []

    async def should_return_422_when_contexte_empty(self, async_client: AsyncClient) -> None:
        """Un contexte vide doit etre rejete (on ne raisonne pas sur le vide)."""
        payload = {
            "requete_id": str(uuid4()),
            "contexte": {},  # aucun bloc
            "regles": [],
            "question": "Test",
            "profondeur_max": 5,
        }
        response = await async_client.post(
            "/api/v1/reasoning/infer",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 422
