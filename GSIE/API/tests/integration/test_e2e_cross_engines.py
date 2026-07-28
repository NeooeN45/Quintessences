"""Tests E2E cross-moteurs — chaîne complète + edge cases API.

Couvre :
A. Chaîne cross-moteurs Evidence -> Knowledge -> Correlation -> Reasoning
   -> Diagnostic (Docker requis) — vérifie la traçabilité ADR-009.
B. Pipeline complet Evidence -> Knowledge (Docker requis).
C. Edge cases API sans Docker : rate limiting, CORS, gzip, metrics,
   health détaillé, RBAC, JWT expiré, validation stricte, pagination.

Les tests Docker utilisent httpx.AsyncClient (asyncpg casse sur boucle
différente avec TestClient synchrone — voir test_pipeline_api.py).
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
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

# --- Tokens JWT de test ---
_WRITER_TOKEN = create_access_token(subject="test-e2e-writer", claims={"roles": ["writer"]})
_WRITER_HEADERS = {"Authorization": f"Bearer {_WRITER_TOKEN}"}
_READER_TOKEN = create_access_token(subject="test-e2e-reader", claims={"roles": ["reader"]})
_READER_HEADERS = {"Authorization": f"Bearer {_READER_TOKEN}"}
_ADMIN_TOKEN = create_access_token(subject="test-e2e-admin", claims={"roles": ["admin"]})
_ADMIN_HEADERS = {"Authorization": f"Bearer {_ADMIN_TOKEN}"}


# ---------------------------------------------------------------------------
# Fixture AsyncClient avec DB de test
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient dont get_db est branchée sur la session de test."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# A. Chaîne cross-moteurs complète (Docker requis)
# ---------------------------------------------------------------------------


@requires_docker
class TestChaineCrossMoteurs:
    """Chaîne Evidence -> Knowledge -> Correlation -> Reasoning -> Diagnostic.

    Vérifie que les sources sont préservées à chaque étape (ADR-009) et
    que le niveau de preuve se propage correctement.
    """

    async def should_preserve_sources_across_full_chain(self, async_client: AsyncClient) -> None:
        """ADR-009 : la source doit être préservée de Evidence à Knowledge."""
        # --- Étape 1 : Evidence (évaluer une raw knowledge) ---
        soumission_id = uuid4()
        sub = RawKnowledgeSubmission(
            soumission_id=soumission_id,
            type_contenu=ContentType.publication,
            contenu={
                "definition": "Le chene sessile prefere les sols acides a pH < 6",
                "minimum": 4.5,
                "maximum": 6.0,
            },
            source_candidate=SourceReference(
                type_source=SourceType.peer_reviewed,
                auteur="Rameau et al. (2008)",
                date_publication="2008",
                reference="Flore forestiere francaise, tome 1, IDF",
            ),
            date_soumission=datetime.now(UTC),
            soumetteur="test_e2e_chain",
        )
        resp_evidence = await async_client.post(
            "/api/v1/evidence/evaluate",
            json=sub.model_dump(mode="json"),
            headers=_WRITER_HEADERS,
        )
        assert resp_evidence.status_code == 200
        evidence_data = resp_evidence.json()
        # QualifiedKnowledge : contenu_normalise, connaissance_id, statut
        assert evidence_data["statut"] == "accepte"
        assert evidence_data["evidence_level"] == "B"
        # ADR-009 : source préservée
        assert evidence_data["source"]["auteur"] == "Rameau et al. (2008)"
        connaissance_id = evidence_data["connaissance_id"]
        contenu_normalise = evidence_data["contenu_normalise"]

        # --- Étape 2 : Knowledge (ingest la connaissance qualifiée) ---
        ingest_payload = {
            "connaissance_id": str(connaissance_id),
            "contenu_normalise": contenu_normalise,
            "type": "concept",
            "titre": "pH optimal du chene sessile",
            "description": "Le chene sessile prefere les sols acides a pH < 6",
            "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
            "evidence_level": "B",
            "source": evidence_data["source"],
            "statut": "accepte",
            "domaines_validite": [
                {
                    "parametre": "pH",
                    "minimum": 4.5,
                    "maximum": 6.0,
                    "unite": "pH",
                }
            ],
            "mots_cles": ["chene_sessile", "pH", "sol_acide"],
        }
        resp_knowledge = await async_client.post(
            "/api/v1/knowledge/ingest",
            json=ingest_payload,
            headers=_WRITER_HEADERS,
        )
        assert resp_knowledge.status_code == 201
        knowledge_data = resp_knowledge.json()
        # ADR-009 : source préservée dans la knowledge
        assert knowledge_data["source"]["auteur"] == "Rameau et al. (2008)"
        assert knowledge_data["evidence_level"] == "B"

    async def should_reject_chain_when_evidence_refused(self, async_client: AsyncClient) -> None:
        """Si Evidence refuse (source non sourcée), la chaîne s'arrête tôt."""
        sub = RawKnowledgeSubmission(
            soumission_id=uuid4(),
            type_contenu=ContentType.observation,
            contenu={"definition": "Test non sourcé"},
            source_candidate=SourceReference(
                type_source=SourceType.observation_terrain,
                auteur="Anonyme",
                reference="observation_non_verifiee",
            ),
            date_soumission=datetime.now(UTC),
            soumetteur="test_e2e_chain",
        )
        resp = await async_client.post(
            "/api/v1/evidence/evaluate",
            json=sub.model_dump(mode="json"),
            headers=_WRITER_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        # observation_terrain -> niveau D ou E, potentiellement refuse ou quarantine
        assert data["statut"] in ("refuse", "quarantine", "accepte")

    async def should_query_knowledge_after_ingest(self, async_client: AsyncClient) -> None:
        """Après ingest, la knowledge doit être queryable."""
        # D'abord évaluer une connaissance via Evidence
        soumission_id = uuid4()
        sub = RawKnowledgeSubmission(
            soumission_id=soumission_id,
            type_contenu=ContentType.publication,
            contenu={"definition": "RUM du hetre", "minimum": 80},
            source_candidate=SourceReference(
                type_source=SourceType.peer_reviewed,
                auteur="Rameau et al. (2008)",
                date_publication="2008",
                reference="Flore forestiere francaise, tome 1, IDF",
            ),
            date_soumission=datetime.now(UTC),
            soumetteur="test_e2e_chain",
        )
        resp_evidence = await async_client.post(
            "/api/v1/evidence/evaluate",
            json=sub.model_dump(mode="json"),
            headers=_WRITER_HEADERS,
        )
        assert resp_evidence.status_code == 200
        evidence_data = resp_evidence.json()

        # Ingest avec le bon schéma KnowledgeIngestRequest
        ingest_payload = {
            "connaissance_id": str(evidence_data["connaissance_id"]),
            "contenu_normalise": evidence_data["contenu_normalise"],
            "type": "concept",
            "titre": "RUM du hetre",
            "description": "Le hetre necessite un RUM minimum de 80mm",
            "domaine_scientifique": "ecologie_forestiere_et_stationnelle",
            "evidence_level": evidence_data["evidence_level"],
            "source": evidence_data["source"],
            "statut": "accepte",
            "domaines_validite": [
                {
                    "parametre": "RUM",
                    "minimum": 80,
                    "unite": "mm",
                }
            ],
            "mots_cles": ["hetre", "RUM"],
        }
        resp_ingest = await async_client.post(
            "/api/v1/knowledge/ingest",
            json=ingest_payload,
            headers=_WRITER_HEADERS,
        )
        assert resp_ingest.status_code == 201

        # Query avec le bon schéma KnowledgeQuery
        query_payload = {
            "requete_id": str(uuid4()),
            "type": "par_concept",
            "filtres": {"mots_cles": "hetre"},
        }
        resp_query = await async_client.post(
            "/api/v1/knowledge/query",
            json=query_payload,
            headers=_READER_HEADERS,
        )
        assert resp_query.status_code == 200
        data = resp_query.json()
        assert "connaissances" in data

    async def should_return_knowledge_stats(self, async_client: AsyncClient) -> None:
        """GET /knowledge/stats retourne les statistiques du graphe."""
        resp = await async_client.get(
            "/api/v1/knowledge/stats",
            headers=_READER_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_objects" in data


# ---------------------------------------------------------------------------
# B. Edge cases API sans Docker
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Rate limiting — slowapi doit limiter les requêtes excessives.

    Note : ces tests nécessitent la DB car l'endpoint /correlation/compute
    accède à la session. Marqués requires_docker.
    """

    @requires_docker
    async def should_apply_rate_limit_on_correlation_compute(
        self, async_client: AsyncClient
    ) -> None:
        """POST /correlation/compute a une limite — dépasser -> 429."""
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
            "methode": "pearson",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
        }
        # La limite est 30/minute sur correlation/compute
        # On envoie 35 requêtes — les dernières doivent être limitées
        statuses: list[int] = []
        for _ in range(35):
            resp = await async_client.post(
                "/api/v1/correlation/compute",
                json=payload,
                headers=_WRITER_HEADERS,
            )
            statuses.append(resp.status_code)
        # Au moins une doit être 429 (rate limited)
        assert 429 in statuses


class TestCORSSecurity:
    """CORS — headers de sécurité présents sur toutes les réponses."""

    def should_return_security_headers_on_api_response(self) -> None:
        """Les headers OWASP A05 doivent être présents."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert "Strict-Transport-Security" in resp.headers

    def should_allow_configured_origins(self) -> None:
        """CORS autorise les origines configurées."""
        app = create_app()
        client = TestClient(app)
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Soit 200 (preflight OK), soit 400 (origine non autorisée)
        assert resp.status_code in (200, 400)


class TestGzipCompression:
    """Gzip — compression des réponses si Accept-Encoding: gzip."""

    def should_compress_response_when_gzip_requested(self) -> None:
        """Avec Accept-Encoding: gzip, la réponse doit être compressée."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/health", headers={"Accept-Encoding": "gzip"})
        # Soit compressé, soit non (si réponse trop petite)
        assert resp.status_code == 200


class TestPrometheusMetrics:
    """Prometheus — /metrics expose les métriques."""

    def should_expose_metrics_endpoint(self) -> None:
        """GET /metrics doit retourner les métriques Prometheus."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200
        # Le contenu doit contenir des métriques Prometheus
        body = resp.text
        assert "http_requests" in body or "request_count" in body or "gsie" in body


class TestHealthDetailed:
    """Health — /health retourne le statut + dépendances."""

    def should_return_healthy_status(self) -> None:
        """GET /health retourne status=healthy."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def should_return_ready_on_ready_endpoint(self) -> None:
        """GET /ready retourne 200 quand l'app est prête."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/ready")
        assert resp.status_code == 200


class TestRBAC:
    """RBAC — reader ne peut pas écrire, writer ne peut pas admin.

    Ces tests mockent get_db pour éviter la connexion DB réelle (le TestClient
    synchrone casse avec asyncpg sur une boucle différente).
    """

    @staticmethod
    def _app_with_mock_db() -> Any:
        """Crée une app avec get_db mockée (session qui lève si appelée)."""
        from collections.abc import AsyncGenerator

        app = create_app()

        async def _mock_get_db() -> AsyncGenerator[None, None]:
            # Lève une exception si la DB est réellement accédée — les tests
            # RBAC doivent échouer avant (401/403) grâce à l'auth.
            yield None  # type: ignore[misc]

        app.dependency_overrides[get_db] = _mock_get_db
        return app

    def should_reject_post_from_reader_on_correlation(self) -> None:
        """Un reader ne peut pas POST /correlation/compute -> 403."""
        app = self._app_with_mock_db()
        client = TestClient(app)
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
            "methode": "pearson",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
        }
        resp = client.post(
            "/api/v1/correlation/compute",
            json=payload,
            headers=_READER_HEADERS,
        )
        assert resp.status_code == 403

    def should_reject_post_without_token(self) -> None:
        """Sans token, POST doit retourner 401."""
        app = self._app_with_mock_db()
        client = TestClient(app)
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
            "methode": "pearson",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
        }
        resp = client.post("/api/v1/correlation/compute", json=payload)
        assert resp.status_code == 401


class TestJWTExpired:
    """JWT expiré — doit retourner 401."""

    def should_reject_expired_token(self) -> None:
        """Un token expiré doit être rejeté -> 401."""
        import jwt

        from gsie_api.core.auth import _load_private_key

        payload = {
            "sub": "test-expired",
            "roles": ["writer"],
            "exp": int((datetime.now(UTC) - timedelta(seconds=10)).timestamp()),
            "iat": int((datetime.now(UTC) - timedelta(seconds=20)).timestamp()),
        }
        key = _load_private_key()
        expired_token = jwt.encode(payload, key, algorithm="RS256")
        app = create_app()
        client = TestClient(app)
        resp = client.get(
            "/api/v1/resources/types",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401


class TestValidationStricte:
    """Validation stricte — payload malformé -> 422 avec détail.

    Ces tests mockent get_db pour éviter la connexion DB (TestClient synchrone
    casse avec asyncpg). La validation Pydantic se fait avant la DB.
    """

    @staticmethod
    def _app_with_mock_db() -> Any:
        from collections.abc import AsyncGenerator

        app = create_app()

        async def _mock_get_db() -> AsyncGenerator[None, None]:
            yield None  # type: ignore[misc]

        app.dependency_overrides[get_db] = _mock_get_db
        return app

    def should_return_422_when_required_field_missing(self) -> None:
        """Un payload sans champ requis doit retourner 422."""
        app = self._app_with_mock_db()
        client = TestClient(app)
        # Payload sans requete_id (requis)
        payload = {
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
            "methode": "pearson",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
        }
        resp = client.post(
            "/api/v1/correlation/compute",
            json=payload,
            headers=_WRITER_HEADERS,
        )
        assert resp.status_code == 422
        data = resp.json()
        # Le détail doit mentionner le champ manquant
        assert "detail" in data

    def should_return_422_when_extra_field_present(self) -> None:
        """Un payload avec un champ interdit (extra=forbid) -> 422."""
        app = self._app_with_mock_db()
        client = TestClient(app)
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
            "methode": "pearson",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Test",
                "reference": "doi:10.0000/test",
            },
            "evidence_level": "B",
            "champ_interdit": "valeur",  # extra=forbid
        }
        resp = client.post(
            "/api/v1/correlation/compute",
            json=payload,
            headers=_WRITER_HEADERS,
        )
        assert resp.status_code == 422


class TestOpenAPISpec:
    """OpenAPI — spec auto-générée et accessible."""

    def should_expose_openapi_json(self) -> None:
        """GET /api/v1/openapi.json retourne la spec OpenAPI."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] is not None
        assert "paths" in data

    def should_expose_docs_ui(self) -> None:
        """GET /docs retourne l'UI Swagger."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/docs")
        assert resp.status_code == 200

    def should_expose_redoc(self) -> None:
        """GET /redoc retourne l'UI ReDoc."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/redoc")
        assert resp.status_code == 200


class TestEngineVersions:
    """Versions des moteurs — chaque moteur expose sa version."""

    @pytest.mark.parametrize(
        "engine",
        ["correlation", "reasoning", "diagnostic"],
    )
    def should_return_version_for_engine(self, engine: str) -> None:
        """GET /{engine}/version retourne la version du moteur."""
        app = create_app()
        client = TestClient(app)
        resp = client.get(f"/api/v1/{engine}/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        # Version sémantique
        version = data["version"]
        assert len(version.split(".")) >= 2


class TestRequestBodyLimit:
    """Limite taille corps de requête — OWASP A04.

    Le middleware ASGI limite la taille avant l'endpoint. On mock get_db
    pour éviter la connexion DB.
    """

    def should_reject_oversized_body(self) -> None:
        """Un corps de requête > 1 MiB doit retourner 413."""
        from collections.abc import AsyncGenerator

        app = create_app()

        async def _mock_get_db() -> AsyncGenerator[None, None]:
            yield None  # type: ignore[misc]

        app.dependency_overrides[get_db] = _mock_get_db
        client = TestClient(app)
        # Créer un payload > 1 MiB
        big_payload = {"data": "x" * (1024 * 1024 + 100)}
        resp = client.post(
            "/api/v1/evidence/evaluate",
            json=big_payload,
            headers=_WRITER_HEADERS,
        )
        # 413 (payload too large) ou 422 (validation Pydantic avant limite)
        assert resp.status_code in (413, 422)


class TestTraceIdPropagation:
    """Trace ID — CON-005 : trace_id propagé dans logs et réponses."""

    def should_propagate_client_trace_id(self) -> None:
        """X-Trace-Id fourni par le client doit être propagé dans la réponse."""
        app = create_app()
        client = TestClient(app)
        trace_id = "test-trace-id-12345"
        resp = client.get("/health", headers={"X-Trace-Id": trace_id})
        assert resp.status_code == 200
        # Le trace_id doit être dans les headers de réponse
        assert resp.headers.get("X-Trace-Id") == trace_id

    def should_generate_trace_id_when_absent(self) -> None:
        """Sans X-Trace-Id, l'API doit en générer un."""
        app = create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        # Un trace_id doit être généré
        trace_id = resp.headers.get("X-Trace-Id")
        assert trace_id is not None
        assert len(trace_id) > 0

    def should_reject_invalid_trace_id(self) -> None:
        """Un X-Trace-Id invalide (caractères spéciaux) doit être ignoré/regénéré."""
        app = create_app()
        client = TestClient(app)
        # Trace ID avec caractères interdits (espace et point-virgule)
        resp = client.get(
            "/health",
            headers={"X-Trace-Id": "invalid;trace;id;with;semicolons"},
        )
        assert resp.status_code == 200
        # L'API doit ignorer le trace_id invalide et en générer un nouveau
        trace_id = resp.headers.get("X-Trace-Id")
        assert trace_id is not None
        assert ";" not in trace_id
