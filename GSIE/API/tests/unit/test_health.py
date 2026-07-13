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

    # Patch des dépendances au niveau du module health
    with patch("gsie_api.core.health.get_db", return_value=mock_db), \
         patch("gsie_api.core.health.get_redis", return_value=mock_redis):
        yield TestClient(app)


def test_health_endpoint_returns_200(client: TestClient):
    """Le endpoint /health doit retourner 200 avec status healthy."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_contains_version(client: TestClient):
    """Le endpoint /health doit contenir la version de l'app."""
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint_contains_dependencies(client: TestClient):
    """Le endpoint /health doit contenir l'état des dépendances."""
    response = client.get("/health")
    data = response.json()
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert "redis" in data["dependencies"]


def test_health_endpoint_has_trace_id_header(client: TestClient):
    """La réponse doit contenir un header X-Trace-Id (CON-005)."""
    response = client.get("/health")
    assert "x-trace-id" in response.headers
    assert len(response.headers["x-trace-id"]) > 0
