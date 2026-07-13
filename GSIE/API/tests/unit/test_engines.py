"""Tests unitaires — endpoints moteurs (status placeholders)."""

from fastapi.testclient import TestClient

from gsie_api.app import create_app

app = create_app()
client = TestClient(app)


def should_return_200_when_evidence_status_requested():
    """Le endpoint /api/v1/evidence/status doit retourner 200."""
    response = client.get("/api/v1/evidence/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "evidence"
    assert data["status"] == "not_implemented"


def should_return_200_when_knowledge_status_requested():
    """Le endpoint /api/v1/knowledge/status doit retourner 200."""
    response = client.get("/api/v1/knowledge/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "knowledge"
    assert data["status"] == "not_implemented"


def should_return_200_when_gis_status_requested():
    """Le endpoint /api/v1/gis/status doit retourner 200."""
    response = client.get("/api/v1/gis/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "gis"
    assert data["status"] == "not_implemented"


def should_return_200_when_openapi_schema_requested():
    """Le schéma OpenAPI doit être disponible à /api/v1/openapi.json."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "GSIE API"


def should_return_200_when_docs_requested():
    """La documentation Swagger doit être accessible en développement."""
    response = client.get("/docs")
    assert response.status_code == 200


def should_have_engine_status_schema_when_openapi_requested():
    """Le schéma OpenAPI doit contenir EngineStatusResponse."""
    response = client.get("/api/v1/openapi.json")
    schema = response.json()
    assert "EngineStatusResponse" in schema.get("components", {}).get("schemas", {})
