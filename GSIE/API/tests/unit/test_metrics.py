"""Tests unitaires — protection de l'endpoint Prometheus /metrics."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import SecretStr

from gsie_api.app import create_app


def _base_settings_mock():
    """Crée un mock minimal de Settings pour `create_app`."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.app_name = "GSIE API"
    mock.app_version = "0.1.0"
    mock.environment = "development"
    mock.debug = False
    mock.log_level = "INFO"
    mock.api_v1_prefix = "/api/v1"
    mock.cors_origins = ["http://localhost:3000"]
    mock.rate_limit_enabled = False
    mock.rate_limit_default = "60/minute"
    mock.rate_limit_storage_url = "memory://"
    mock.otel_enabled = False
    mock.max_request_body_size = 1_048_576
    mock.metrics_bearer_token = SecretStr("")
    return mock


def should_allow_metrics_in_development_without_token():
    """En développement sans token, /metrics est public pour le dev local."""
    with patch("gsie_api.app._settings", _base_settings_mock()):
        app = create_app()
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text


def should_deny_metrics_with_wrong_bearer_token():
    """Si GSIE_METRICS_BEARER_TOKEN est défini, un token invalide est refusé."""
    mock = _base_settings_mock()
    mock.metrics_bearer_token = SecretStr("prometheus-token")

    with patch("gsie_api.app._settings", mock):
        app = create_app()
        client = TestClient(app)

        response = client.get("/metrics")
        assert response.status_code == 401

        response = client.get(
            "/metrics",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401


def should_allow_metrics_with_valid_bearer_token():
    """Un scraper Prometheus avec le bon Bearer token accède à /metrics."""
    mock = _base_settings_mock()
    mock.metrics_bearer_token = SecretStr("prometheus-token")

    with patch("gsie_api.app._settings", mock):
        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/metrics",
            headers={"Authorization": "Bearer prometheus-token"},
        )
        assert response.status_code == 200
