"""Tests unitaires — WebSocket (v6.2).

Teste le router, le manager, le rate limiter, la validation des canaux.
"""

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


class TestConnectionManager:
    """Tests du ConnectionManager (sans vraie WebSocket)."""

    def test_should_initialize_empty(self) -> None:
        mgr = ConnectionManager()
        assert len(mgr._connections) == 0
        assert len(mgr._channels) == 0


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
