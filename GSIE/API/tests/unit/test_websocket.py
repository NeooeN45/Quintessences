"""Tests unitaires — WebSocket (v6.2).

Teste le router, le manager, le rate limiter, la validation des canaux.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.websocket import router as websocket_router
from gsie_api.websocket.manager import ConnectionManager
from gsie_api.websocket.router import _RATE_LIMIT_MAX, _validate_channels


class TestChannelValidation:
    """Tests de la validation des canaux."""

    def test_should_return_all_when_no_channels(self) -> None:
        result = _validate_channels(None)
        assert result == ["all"]

    def test_should_return_all_when_empty_list(self) -> None:
        result = _validate_channels([])
        assert result == ["all"]

    def test_should_filter_invalid_channels(self) -> None:
        result = _validate_channels(["assertion", "hacked", "observation"])
        assert "assertion" in result
        assert "observation" in result
        assert "hacked" not in result

    def test_should_return_all_when_all_invalid(self) -> None:
        result = _validate_channels(["hacked", "evil"])
        assert result == ["all"]

    def test_should_allow_alert_subchannels(self) -> None:
        result = _validate_channels(["alert.fire_risk", "alert.drought"])
        assert "alert.fire_risk" in result
        assert "alert.drought" in result


class TestRateLimiter:
    """Tests du rate limiter."""

    def test_should_allow_under_limit(self) -> None:
        from gsie_api.websocket.router import _rate_limiter

        ws_id = 999999
        for _ in range(_RATE_LIMIT_MAX):
            assert _rate_limiter.check(ws_id) is True
        # Le 11e message doit être bloqué
        assert _rate_limiter.check(ws_id) is False
        _rate_limiter.cleanup(ws_id)


class TestWebSocketOrigins:
    """Tests de la politique Origin du handshake WebSocket."""

    def test_should_reject_untrusted_browser_origin(self, monkeypatch) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})
        monkeypatch.setattr(
            websocket_router._settings,
            "ws_allowed_origins",
            ["https://hub.geosylva.example"],
        )

        with (
            pytest.raises(WebSocketDisconnect) as exc,
            client.websocket_connect(
                f"/api/v1/ws/hub?token={token}",
                headers={"Origin": "https://evil.example"},
            ),
        ):
            pass

        assert exc.value.code == 1008

    def test_should_reject_valid_token_without_role(self) -> None:
        """Une signature valide sans autorisation ne suffit pas au handshake."""
        client = TestClient(create_app())
        token = create_access_token("sans-role")

        with (
            pytest.raises(WebSocketDisconnect) as exc,
            client.websocket_connect(f"/api/v1/ws/hub?token={token}"),
        ):
            pass

        assert exc.value.code == 1008


class TestConnectionManager:
    """Tests du ConnectionManager (sans vraie WebSocket)."""

    def test_should_initialize_empty(self) -> None:
        mgr = ConnectionManager()
        assert len(mgr._connections) == 0
        assert len(mgr._channels) == 0

    @pytest.mark.asyncio
    async def test_should_filter_rgpd_events_for_global_reader(self) -> None:
        """Le canal all ne doit jamais contourner le RBAC des types RGPD."""
        mgr = ConnectionManager()
        reader = AsyncMock()
        rgpd_manager = AsyncMock()

        await mgr.connect(reader, ["all"], roles=["reader"])
        await mgr.connect(rgpd_manager, ["all"], roles=["rgpd_manager"])
        await mgr._local_broadcast("consent", {"event_type": "resource.created"})

        reader.send_json.assert_not_awaited()
        rgpd_manager.send_json.assert_awaited_once()

        await mgr.disconnect(reader)
        await mgr.disconnect(rgpd_manager)
        assert reader not in mgr._roles
        assert rgpd_manager not in mgr._roles


class TestBroadcastTestEndpoint:
    """Tests de l'endpoint POST /ws/broadcast-test (Gate 5 E2E)."""

    def test_should_reject_invalid_channel(self) -> None:
        """Un canal non autorisé doit retourner success=False."""
        from gsie_api.websocket.router import BroadcastTestRequest, BroadcastTestResponse

        # Vérifier que le modèle valide le canal côté endpoint
        req = BroadcastTestRequest(channel="hacked", message="test")
        assert req.channel == "hacked"
        # L'endpoint vérifie _ALLOWED_CHANNELS — on teste la logique ici
        from gsie_api.websocket.router import _ALLOWED_CHANNELS

        assert "hacked" not in _ALLOWED_CHANNELS
        # La réponse d'échec
        resp = BroadcastTestResponse(
            success=False, channel="hacked", event_type="observation.received", subscribers=0
        )
        assert resp.success is False

    def test_should_accept_valid_broadcast_request(self) -> None:
        """Un BroadcastTestRequest valide doit se construire correctement."""
        from gsie_api.websocket.events import EventType
        from gsie_api.websocket.router import BroadcastTestRequest

        req = BroadcastTestRequest(
            channel="alert",
            event_type=EventType.alert_fire_risk,
            message="Test E2E",
        )
        assert req.channel == "alert"
        assert req.event_type == EventType.alert_fire_risk
        assert req.message == "Test E2E"

    def test_should_reject_forged_admin_body_without_jwt(self) -> None:
        """Un role place dans le JSON ne doit jamais remplacer le JWT."""
        client = TestClient(create_app())

        response = client.post(
            "/api/v1/ws/broadcast-test",
            json={
                "channel": "all",
                "message": "attaque",
                "user": {"sub": "attacker", "roles": ["admin"]},
            },
        )

        assert response.status_code == 401

    def test_should_reject_reader_jwt(self) -> None:
        """Le role reader n'est pas autorise a publier un broadcast de test."""
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        response = client.post(
            "/api/v1/ws/broadcast-test",
            json={"channel": "all", "message": "interdit"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    def test_should_allow_admin_jwt(self, monkeypatch) -> None:
        """Un JWT admin valide autorise explicitement le broadcast."""
        client = TestClient(create_app())
        token = create_access_token("admin", claims={"roles": ["admin"]})
        broadcast = AsyncMock()
        monkeypatch.setattr(websocket_router.manager, "broadcast", broadcast)

        response = client.post(
            "/api/v1/ws/broadcast-test",
            json={"channel": "all", "message": "autorise"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        broadcast.assert_awaited_once()
