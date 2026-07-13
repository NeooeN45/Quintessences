"""Tests unitaires — endpoints health/ready (sans dépendances externes)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Client de test FastAPI — mock des dépendances DB et Redis."""
    from unittest.mock import AsyncMock, MagicMock

    from gsie_api.app import create_app
    from gsie_api.infrastructure.database import get_db
    from gsie_api.infrastructure.health import _READY_CACHE_KEY
    from gsie_api.infrastructure.redis_client import get_redis

    app = create_app()

    # Mock get_db : retourne une session mock
    # scalar_one est synchrone (MagicMock, pas AsyncMock)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one=MagicMock(return_value="3.4.2"))
    )

    # Mock get_redis : retourne un client mock (ping + get/setex pour cache)
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)  # Pas de cache
    mock_redis.setex = AsyncMock(return_value=True)

    # Override des dépendances FastAPI (méthode correcte vs patch)
    async def _mock_get_db():
        yield mock_db

    async def _mock_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _mock_get_db
    app.dependency_overrides[get_redis] = _mock_get_redis

    yield TestClient(app)

    app.dependency_overrides.clear()


def should_return_200_when_liveness_checked(client: TestClient):
    """/health (liveness) doit retourner 200 instantanément sans DB."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def should_return_empty_dependencies_when_liveness(client: TestClient):
    """/health (liveness) ne doit pas vérifier les dépendances."""
    response = client.get("/health")
    data = response.json()
    assert data["dependencies"] == {}


def should_return_200_when_readiness_checked(client: TestClient):
    """/ready (readiness) doit retourner 200 avec DB+Redis healthy."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def should_contain_dependencies_when_readiness_responds(client: TestClient):
    """/ready doit contenir l'état des dépendances DB et Redis."""
    response = client.get("/ready")
    data = response.json()
    assert "database" in data["dependencies"]
    assert "redis" in data["dependencies"]


def should_contain_version_when_health_responds(client: TestClient):
    """Le endpoint /health doit contenir la version de l'app."""
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"


def should_have_trace_id_header_when_responding(client: TestClient):
    """La réponse doit contenir un header X-Trace-Id (CON-005)."""
    response = client.get("/health")
    assert "x-trace-id" in response.headers
    assert len(response.headers["x-trace-id"]) > 0


def should_have_security_headers_when_responding(client: TestClient):
    """La réponse doit contenir les headers de sécurité (OWASP A05)."""
    response = client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "strict-transport-security" in response.headers
    assert "content-security-policy" in response.headers
    assert "permissions-policy" in response.headers


def should_reject_invalid_trace_id_when_header_contains_script(client: TestClient):
    """Un X-Trace-Id contenant du HTML doit être ignoré (anti-injection)."""
    response = client.get("/health", headers={"X-Trace-Id": "<script>alert(1)</script>"})
    trace_id = response.headers.get("x-trace-id", "")
    assert "<script>" not in trace_id
    assert len(trace_id) > 0


def should_not_expose_server_header_when_responding(client: TestClient):
    """Le header Server ne doit pas être exposé (anti-fingerprinting)."""
    response = client.get("/health")
    assert "server" not in {k.lower() for k in response.headers.keys()}


def should_return_413_when_body_too_large(client: TestClient):
    """Une requête avec un corps trop large doit retourner 413."""
    large_body = "x" * (2 * 1024 * 1024)  # 2 MiB > limite 1 MiB
    response = client.post(
        "/health",
        content=large_body,
        headers={"content-length": str(len(large_body))},
    )
    assert response.status_code == 413
