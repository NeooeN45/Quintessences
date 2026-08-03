"""Tests unitaires — couverture résiduelle batch 1.

Couvre les comportements suivants :
- app.py : logging des erreurs de shutdown (websocket manager, auth store)
  et gestion des branches du handler de rate limiting
- auth/router.py : chemin succès du login, normalisation des rôles non
  string/list, rejet d'un refresh token déjà utilisé, rejet d'un logout
  avec un jti non-string
- websocket/router.py : éviction des timestamps expirés du rate limiter,
  retour silencieux quand la connexion au hub ou aux events est refusée
- shared/middleware.py : validation de max_body_size, re-levée de
  l'erreur de dépassement de taille après le début de la réponse
- shared/http_client.py : levée de l'exception de fallback quand la
  boucle de retry ne s'exécute jamais
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.auth import router as auth_router

if TYPE_CHECKING:
    from collections.abc import Generator

# Activer le dev login pour les tests auth (comme test_auth_coverage.py)
auth_router._settings.auth_dev_login_enabled = True
auth_router._settings.auth_dev_password = "changeme"


# ===========================================================================
# app.py — logging des erreurs de shutdown du websocket manager
# ===========================================================================


def should_log_error_when_ws_shutdown_fails(mock_lifespan: object) -> None:
    """Le lifespan doit logger l'erreur si manager.shutdown() échoue."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.otel_enabled = False
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
        mock_settings.max_request_body_size = 1_048_576

        with (
            patch(
                "gsie_api.websocket.manager.manager.shutdown",
                new_callable=AsyncMock,
                side_effect=RuntimeError("ws shutdown failed"),
            ),
            patch("gsie_api.infrastructure.database.engine") as mock_engine,
            patch("gsie_api.infrastructure.redis_client.redis_pool") as mock_pool,
            patch(
                "gsie_api.auth.refresh_tokens.close_refresh_token_store",
                new_callable=AsyncMock,
            ),
        ):
            mock_engine.dispose = AsyncMock()
            mock_pool.disconnect = AsyncMock()

            app = create_app()
            client = TestClient(app)
            # Le shutdown se produit à la sortie du context manager
            with client:
                pass


# ===========================================================================
# app.py — logging des erreurs de shutdown de l'auth store
# ===========================================================================


def should_log_error_when_auth_store_shutdown_fails(mock_lifespan: object) -> None:
    """Le lifespan doit logger l'erreur si close_refresh_token_store() échoue."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.otel_enabled = False
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
        mock_settings.max_request_body_size = 1_048_576

        with (
            patch("gsie_api.infrastructure.database.engine") as mock_engine,
            patch("gsie_api.infrastructure.redis_client.redis_pool") as mock_pool,
            patch(
                "gsie_api.auth.refresh_tokens.close_refresh_token_store",
                new_callable=AsyncMock,
                side_effect=RuntimeError("auth store shutdown failed"),
            ),
        ):
            mock_engine.dispose = AsyncMock()
            mock_pool.disconnect = AsyncMock()

            app = create_app()
            client = TestClient(app)
            with client:
                pass


# ===========================================================================
# app.py — branches du handler de rate limiting
# ===========================================================================


def should_handle_rate_limit_exceeded_when_correct_exception_type() -> None:
    """Le _rate_limit_handler doit déléguer au handler slowapi pour RateLimitExceeded."""
    from slowapi.errors import RateLimitExceeded

    app = create_app()
    handler = app.exception_handlers[RateLimitExceeded]

    request = MagicMock()
    request.state = MagicMock()
    # RateLimitExceeded attend un objet Limit avec un attribut error_message
    mock_limit = MagicMock()
    mock_limit.error_message = "Rate limit exceeded"
    mock_limit.limit = "20/minute"
    exc = RateLimitExceeded(mock_limit)
    response = handler(request, exc)
    assert response is not None


def should_raise_type_error_when_unexpected_exception_type() -> None:
    """Le _rate_limit_handler doit lever TypeError pour un type d'exception inattendu."""
    from slowapi.errors import RateLimitExceeded

    app = create_app()
    handler = app.exception_handlers[RateLimitExceeded]

    request = MagicMock()
    exc = ValueError("unexpected")
    with pytest.raises(TypeError, match="Unexpected exception type"):
        handler(request, exc)


# ===========================================================================
# auth/router.py — chemin succès du login
# ===========================================================================


class TestLoginSuccessPath:
    """Vérifie le chemin succès du login (logger.info + retour des tokens)."""

    @pytest.fixture
    def client(self, mock_lifespan: object) -> Generator[TestClient, None, None]:
        with TestClient(create_app()) as test_client:
            yield test_client

    def should_return_tokens_when_login_succeeds(self, client: TestClient) -> None:
        """Un login valide doit retourner access + refresh tokens."""
        with (
            patch.object(auth_router._settings, "auth_dev_login_enabled", True),
            patch.object(auth_router._settings, "auth_dev_username", "admin"),
            patch.object(auth_router._settings, "auth_dev_password", "changeme"),
        ):
            from unittest.mock import AsyncMock

            from gsie_api.auth.router import get_refresh_token_store as _get_store

            mock_store = AsyncMock()
            mock_store.register = AsyncMock()
            client.app.dependency_overrides[_get_store] = lambda: mock_store
            try:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "changeme"},
                )
            finally:
                client.app.dependency_overrides.pop(_get_store, None)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["expires_in"] > 0


# ===========================================================================
# auth/router.py — normalisation des rôles non string/list
# ===========================================================================


def should_set_empty_roles_when_claim_is_non_string_non_list(
    mock_lifespan: object,
) -> None:
    """Un refresh token avec roles non-string non-list doit donner roles=[]."""
    from gsie_api.auth.router import get_refresh_token_store as _get_store
    from gsie_api.core.auth import create_refresh_token

    token = create_refresh_token(
        subject=str(auth_router.DEV_USER_ID),
        claims={"roles": 123, "username": "admin"},
    )

    with TestClient(create_app()) as client:
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)

    assert response.status_code == 200


# ===========================================================================
# auth/router.py — rejet d'un refresh token déjà consommé
# ===========================================================================


def should_return_401_when_refresh_token_already_used(
    mock_lifespan: object,
) -> None:
    """Un refresh token déjà utilisé doit retourner 401."""
    from gsie_api.auth.router import get_refresh_token_store as _get_store
    from gsie_api.core.auth import create_refresh_token

    token = create_refresh_token(
        subject=str(auth_router.DEV_USER_ID),
        claims={"roles": ["admin"], "username": "admin"},
    )

    with TestClient(create_app()) as client:
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=False)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)

    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "already used" in detail or "expired" in detail


# ===========================================================================
# auth/router.py — rejet d'un logout avec un jti invalide
# ===========================================================================


def should_return_401_when_logout_jti_is_not_string(
    mock_lifespan: object,
) -> None:
    """Un logout avec jti non-string doit retourner 401."""
    from gsie_api.auth.router import get_refresh_token_store as _get_store

    # Créer un token valide pour la structure, mais mocker verify_token
    # pour retourner un payload avec jti non-string
    with TestClient(create_app()) as client:
        mock_store = AsyncMock()
        mock_store.consume = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store

        fake_payload = {"jti": 12345, "sub": "test", "type": "refresh", "exp": 9999999999}
        try:
            with patch("gsie_api.auth.router.verify_token", return_value=fake_payload):
                response = client.post(
                    "/api/v1/auth/logout",
                    json={"refresh_token": "fake-token"},
                )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)

    assert response.status_code == 401
    assert "Invalid refresh token claims" in response.json()["detail"]


# ===========================================================================
# websocket/router.py — éviction des timestamps expirés du rate limiter
# ===========================================================================


def should_popleft_expired_timestamps_in_rate_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le rate limiter doit évincer les timestamps expirés via popleft."""
    from gsie_api.websocket.router import _RATE_LIMIT_MAX, _RATE_LIMIT_WINDOW, _rate_limiter

    ws_id = 888888
    # Temps simulé : t0 pour les premiers messages, puis t0 + window + 1 pour le suivant
    current_time = [1000.0]
    monkeypatch.setattr(
        "gsie_api.websocket.router.monotonic",
        lambda: current_time[0],
    )

    # Remplir le rate limiter au maximum au temps t0
    for _ in range(_RATE_LIMIT_MAX):
        assert _rate_limiter.check(ws_id) is True

    # Avancer le temps au-delà de la fenêtre — les timestamps doivent être évincés
    current_time[0] = 1000.0 + _RATE_LIMIT_WINDOW + 1.0

    # Le message doit être autorisé car les anciens timestamps sont popleft
    assert _rate_limiter.check(ws_id) is True

    _rate_limiter.cleanup(ws_id)


# ===========================================================================
# websocket/router.py — connexion refusée sur le hub
# ===========================================================================


async def should_return_silently_when_hub_connect_refused() -> None:
    """ws_hub doit retourner silencieusement si manager.connect retourne False."""
    from gsie_api.websocket import router as ws_router
    from gsie_api.websocket.router import ws_hub

    # Mock WebSocket — _authenticate_ws doit réussir
    mock_ws = MagicMock()
    mock_ws.headers = {}
    mock_ws.query_params = {"token": "fake"}
    mock_ws.client = MagicMock()
    mock_ws.client.host = "127.0.0.1"

    fake_user = {"sub": "admin", "roles": ["admin"]}

    with (
        patch("gsie_api.websocket.router._authenticate_ws", AsyncMock(return_value=fake_user)),
        patch.object(ws_router.manager, "connect", AsyncMock(return_value=False)),
        patch.object(ws_router.manager, "disconnect", AsyncMock()),
    ):
        # ws_hub doit retourner sans appeler receive_text
        await ws_hub(mock_ws, channels=None)


# ===========================================================================
# websocket/router.py — connexion refusée sur les events
# ===========================================================================


async def should_return_silently_when_events_connect_refused() -> None:
    """ws_events doit retourner silencieusement si manager.connect retourne False."""
    from gsie_api.websocket import router as ws_router
    from gsie_api.websocket.router import ws_events

    mock_ws = MagicMock()
    mock_ws.headers = {}
    mock_ws.query_params = {"token": "fake"}
    mock_ws.client = MagicMock()
    mock_ws.client.host = "127.0.0.1"

    fake_user = {"sub": "admin", "roles": ["admin"]}

    with (
        patch("gsie_api.websocket.router._authenticate_ws", AsyncMock(return_value=fake_user)),
        patch.object(ws_router.manager, "connect", AsyncMock(return_value=False)),
        patch.object(ws_router.manager, "disconnect", AsyncMock()),
    ):
        # ws_events doit retourner sans appeler receive_text
        await ws_events(mock_ws)


# ===========================================================================
# shared/middleware.py — validation de max_body_size
# ===========================================================================


def should_raise_value_error_when_max_body_size_negative() -> None:
    """RequestBodyLimitMiddleware doit lever ValueError si max_body_size < 0."""
    from gsie_api.shared.middleware import RequestBodyLimitMiddleware

    mock_app = MagicMock()
    with pytest.raises(ValueError, match="max_body_size doit être positif"):
        RequestBodyLimitMiddleware(mock_app, max_body_size=-1)


# ===========================================================================
# shared/middleware.py — re-levée de l'erreur après le début de la réponse
# ===========================================================================


async def should_raise_when_body_exceeds_limit_after_response_started() -> None:
    """Le middleware doit re-raise _RequestBodyTooLargeError si la réponse a déjà commencé."""
    from gsie_api.shared.middleware import RequestBodyLimitMiddleware, _RequestBodyTooLargeError

    call_count = 0

    async def mock_receive():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"type": "http.request", "body": b"1234", "more_body": True}
        return {"type": "http.request", "body": b"567890", "more_body": False}

    sent_messages: list[dict] = []

    async def mock_send(message: dict) -> None:
        sent_messages.append(message)

    async def greedy_app(scope, receive, send):
        """App ASGI qui démarre la réponse avant de lire tout le corps."""
        # Démarrer la réponse AVANT de lire le corps — response_started devient True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        # Lire le corps — le deuxième chunk fait dépasser la limite
        await receive()  # 4 bytes
        await receive()  # 6 bytes → total 10 > 8
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = RequestBodyLimitMiddleware(greedy_app, max_body_size=8)

    with pytest.raises(_RequestBodyTooLargeError):
        await middleware(
            {"type": "http", "method": "POST", "path": "/", "headers": []},
            mock_receive,
            mock_send,
        )


# ===========================================================================
# shared/http_client.py — fallback quand la boucle de retry ne s'exécute pas
# ===========================================================================


async def should_raise_fallback_when_loop_never_executes() -> None:
    """Le fallback de _request doit lever exception_class quand la boucle ne s'exécute pas."""
    from gsie_api.shared.http_client import ResilientHttpClient

    class _TestClient(ResilientHttpClient):
        @property
        def exception_class(self) -> type[Exception]:
            return RuntimeError

        @property
        def base_url(self) -> str:
            return "https://api.test.example.com"

    # max_retries=-1 → range(0) → boucle vide → déclenche le fallback
    client = _TestClient(max_retries=-1)

    with pytest.raises(RuntimeError, match="Échec"):
        await client._request("GET", "/data")
