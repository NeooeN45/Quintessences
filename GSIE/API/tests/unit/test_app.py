"""Tests unitaires — application FastAPI (app.py)."""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gsie_api.app import create_app


def should_create_app_with_correct_title():
    """create_app doit retourner une FastAPI avec le bon titre."""
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "GSIE API"


def should_have_health_and_ready_routes():
    """L'app doit avoir les routes /health et /ready."""
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/health" in paths
    assert "/ready" in paths


def should_have_engine_routes():
    """L'app doit avoir les routes moteurs sous /api/v1/."""
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/api/v1/evidence/status" in paths
    assert "/api/v1/knowledge/status" in paths
    assert "/api/v1/gis/status" in paths


def should_trigger_lifecycle_when_started():
    """Le lifespan doit démarrer et arrêter l'API avec logs."""
    app = create_app()
    with TestClient(app) as client:
        # Si le lifespan s'exécute sans erreur, on obtient une réponse
        response = client.get("/health")
        assert response.status_code == 200


def should_disable_docs_when_production():
    """En production, /docs et /redoc doivent retourner 404."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.app_name = "GSIE API"
        mock_settings.app_version = "0.1.0"
        mock_settings.environment = "production"
        mock_settings.log_level = "INFO"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.rate_limit_enabled = False
        mock_settings.rate_limit_default = "60/minute"

        app = create_app()
        client = TestClient(app)

        response = client.get("/docs")
        assert response.status_code == 404

        response = client.get("/redoc")
        assert response.status_code == 404


def should_return_404_with_custom_handler_when_unknown_route():
    """Une route inconnue doit retourner 404 avec error_code."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"


def should_compress_response_when_gzip_enabled():
    """Les réponses > 500 bytes doivent être compressées avec Gzip."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert response.headers.get("content-encoding") == "gzip"


def should_return_500_with_error_code_when_unhandled_exception():
    """Le handler global 500 doit retourner 500 sans stack trace (RFC 7807)."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.app_name = "GSIE API"
        mock_settings.app_version = "0.1.0"
        mock_settings.environment = "development"
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.rate_limit_enabled = False
        mock_settings.rate_limit_default = "60/minute"
        mock_settings.rate_limit_storage_url = "memory://"
        mock_settings.otel_enabled = False
        mock_settings.max_request_body_size = 1_048_576

        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)

        # Provoquer une exception non gérée en mockant le router evidence
        with patch("gsie_api.engines.evidence.router.evaluate", side_effect=RuntimeError("boom")):
            from gsie_api.engines.evidence.schemas import (
                ContentType,
                RawKnowledgeSubmission,
                SourceReference,
                SourceType,
            )
            from uuid import uuid4
            from datetime import UTC, datetime

            sub = RawKnowledgeSubmission(
                soumission_id=uuid4(),
                type_contenu=ContentType.publication,
                contenu={"test": "data"},
                source_candidate=SourceReference(
                    type_source=SourceType.peer_reviewed,
                    auteur="Test",
                    reference="DOI:test",
                ),
                date_soumission=datetime.now(UTC),
                soumetteur="test",
            )
            response = client.post(
                "/api/v1/evidence/evaluate",
                json=sub.model_dump(mode="json"),
            )
            assert response.status_code == 500
            # La stack trace ne doit pas être divulguée dans la réponse
            assert "RuntimeError" not in response.text
            assert "boom" not in response.text
            # RFC 7807 Problem Details
            data = response.json()
            assert data["title"] == "Internal Server Error"
            assert data["status"] == 500
            assert data["error_code"] == "INTERNAL_ERROR"
            assert "instance" in data
