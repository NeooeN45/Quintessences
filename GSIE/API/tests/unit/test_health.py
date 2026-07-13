"""Tests unitaires — endpoint health (sans dépendances externes)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Client de test FastAPI — mock des dépendances DB et Redis."""
    from unittest.mock import AsyncMock, patch

    from gsie_api.app import create_app

    app = create_app()

    # Mock get_db : retourne une session mock
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=AsyncMock(scalar_one=AsyncMock(return_value="3.4.2")))

    # Mock get_redis : retourne un client mock
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides = {}

    # Patch des dépendances au niveau du module health (infrastructure)
    with patch("gsie_api.infrastructure.health.get_db", return_value=mock_db), \
         patch("gsie_api.infrastructure.health.get_redis", return_value=mock_redis):
        yield TestClient(app)


def should_return_200_when_health_checked(client: TestClient):
    """Le endpoint /health doit retourner 200 avec status healthy."""
    response = client.get("/health")
    assert response.status_code == 200


def should_contain_version_when_health_responds(client: TestClient):
    """Le endpoint /health doit contenir la version de l'app."""
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"


def should_contain_dependencies_when_health_responds(client: TestClient):
    """Le endpoint /health doit contenir l'état des dépendances."""
    response = client.get("/health")
    data = response.json()
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert "redis" in data["dependencies"]


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


def should_reject_invalid_trace_id_when_header_contains_script(client: TestClient):
    """Un X-Trace-Id contenant du HTML doit être ignoré (anti-injection)."""
    response = client.get("/health", headers={"X-Trace-Id": "<script>alert(1)</script>"})
    trace_id = response.headers.get("x-trace-id", "")
    # Le trace_id doit être un UUID généré, pas le script injecté
    assert "<script>" not in trace_id
    assert len(trace_id) > 0
