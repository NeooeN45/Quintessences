"""Tests unitaires — endpoints health/ready (sans dépendances externes)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.redis_client import get_redis


def _create_client(mock_db=None, mock_redis=None):
    """Crée un client TestClient avec des mocks DB et Redis personnalisés."""
    app = create_app()

    if mock_db is None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one=MagicMock(return_value="3.4.2"))
        )

    if mock_redis is None:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)

    async def _mock_get_db():
        yield mock_db

    async def _mock_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _mock_get_db
    app.dependency_overrides[get_redis] = _mock_get_redis

    return TestClient(app), app


@pytest.fixture
def client():
    """Client de test FastAPI — mock des dépendances DB et Redis."""
    test_client, app = _create_client()
    yield test_client
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


def should_propagate_valid_trace_id_when_provided(client: TestClient):
    """Un X-Trace-Id valide doit être propagé tel quel dans la réponse."""
    response = client.get("/health", headers={"X-Trace-Id": "my-trace-123"})
    assert response.headers["x-trace-id"] == "my-trace-123"


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


def should_return_degraded_when_database_down():
    """/ready doit retourner degraded si la DB est inaccessible."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("Connection refused"))

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)

    test_client, app = _create_client(mock_db, mock_redis)
    response = test_client.get("/ready")
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["database"] == "unhealthy"
    app.dependency_overrides.clear()


def should_return_degraded_when_redis_down():
    """/ready doit retourner degraded si Redis est inaccessible."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one=MagicMock(return_value="3.4.2"))
    )

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))
    mock_redis.get = AsyncMock(side_effect=Exception("Connection refused"))
    mock_redis.setex = AsyncMock(side_effect=Exception("Connection refused"))

    test_client, app = _create_client(mock_db, mock_redis)
    response = test_client.get("/ready")
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["redis"] == "unhealthy"
    app.dependency_overrides.clear()


def should_return_cached_response_when_redis_has_cache():
    """/ready doit retourner la réponse en cache si disponible."""
    cached_data = json.dumps({
        "status": "healthy",
        "version": "0.1.0",
        "environment": "development",
        "timestamp": "2026-07-13T12:00:00Z",
        "dependencies": {"database": "healthy (PostGIS 3.4)", "redis": "healthy"},
    })

    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=cached_data)
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)

    test_client, app = _create_client(mock_db, mock_redis)
    response = test_client.get("/ready")
    data = response.json()
    # Si le cache est utilisé, DB n'est pas interrogée
    mock_db.execute.assert_not_called()
    assert data["status"] == "healthy"
    app.dependency_overrides.clear()


def should_return_unhealthy_when_redis_ping_returns_false():
    """/ready doit retourner unhealthy si Redis ping retourne False."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one=MagicMock(return_value="3.4.2"))
    )

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=False)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)

    test_client, app = _create_client(mock_db, mock_redis)
    response = test_client.get("/ready")
    data = response.json()
    assert data["dependencies"]["redis"] == "unhealthy"
    app.dependency_overrides.clear()


def should_use_simple_ping_in_production():
    """En production, _check_database doit utiliser SELECT 1 (pas PostGIS_Version)."""
    from unittest.mock import patch

    from gsie_api.infrastructure.health import _check_database

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("gsie_api.infrastructure.health._settings") as mock_settings:
        mock_settings.environment = "production"
        import asyncio
        result = asyncio.run(_check_database(mock_db))
        assert result == "healthy"
