"""Tests unitaires -- couverture infrastructure (WebSocket, object_storage, auth, outbox).

Comble les lignes manquantes des modules d'infrastructure pour atteindre 90%+ :
- websocket/manager.py (ConnectionManager : Redis Pub/Sub, heartbeat, broadcast, shutdown)
- websocket/router.py (endpoints /hub et /events, auth WS, rate limiting, broadcast-test)
- infrastructure/object_storage.py (LocalStorage CRUD, S3Storage NotImplementedError, factory)
- auth/refresh_tokens.py (Memory + Redis store : register, consume, rotate, close, factory)
- engines/climate/dpclim_client.py (client HTTP Météo-France : fetch, parse, errors, polling)
- seeds/run_seeds.py (refus explicite du seed v6.1 retire)
- outbox_worker.py (run_worker, main, _publish_to_redis, requeue edge cases)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.websocket import router as websocket_router
from gsie_api.websocket.manager import ConnectionManager

# `gsie_api.websocket.manager` désigne aussi le singleton exporté par le
# paquet, qui masque le module : on passe donc par sys.modules pour obtenir
# bien le module et pouvoir en ajuster les constantes.
manager_module = sys.modules[ConnectionManager.__module__]


# =====================================================================
# WebSocket Manager -- ConnectionManager
# =====================================================================


class TestConnectionManagerRedis:
    """Tests du fan-out Redis Pub/Sub du ConnectionManager."""

    @pytest.mark.asyncio
    async def should_return_none_when_redis_unavailable(self) -> None:
        mgr = ConnectionManager()
        with patch(
            "gsie_api.infrastructure.redis_client.get_redis",
            new_callable=AsyncMock,
            side_effect=ConnectionError("redis down"),
        ):
            result = await mgr._get_redis()
        assert result is None

    @pytest.mark.asyncio
    async def should_return_redis_when_available(self) -> None:
        mgr = ConnectionManager()
        fake_redis = AsyncMock()
        with patch(
            "gsie_api.infrastructure.redis_client.get_redis",
            new_callable=AsyncMock,
            return_value=fake_redis,
        ):
            result = await mgr._get_redis()
        assert result is fake_redis

    @pytest.mark.asyncio
    async def should_not_start_subscriber_when_redis_unavailable(self) -> None:
        mgr = ConnectionManager()
        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=None):
            await mgr.start_redis_subscriber()
        assert mgr._pubsub_task is None

    @pytest.mark.asyncio
    async def should_not_start_subscriber_when_already_started(self) -> None:
        mgr = ConnectionManager()
        mgr._pubsub_task = asyncio.create_task(asyncio.sleep(100))
        try:
            with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=AsyncMock()):
                await mgr.start_redis_subscriber()
        finally:
            mgr._pubsub_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await mgr._pubsub_task
            mgr._pubsub_task = None

    @pytest.mark.asyncio
    async def should_start_subscriber_task_when_redis_available(self) -> None:
        mgr = ConnectionManager()
        fake_redis = AsyncMock()
        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis):
            await mgr.start_redis_subscriber()
        assert mgr._pubsub_task is not None
        await mgr.shutdown()

    @pytest.mark.asyncio
    async def should_stop_subscriber_loop_when_redis_none(self) -> None:
        mgr = ConnectionManager()
        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=None):
            await mgr._redis_subscriber_loop()

    @pytest.mark.asyncio
    async def should_process_redis_pmessage_and_broadcast_locally(self) -> None:
        mgr = ConnectionManager()
        processed = asyncio.Event()

        messages = [
            {"type": "pmessage", "channel": b"gsie:ws:phenomenon", "data": b'{"event_type":"test"}'}
        ]

        async def fake_get_message(timeout=None):
            if messages:
                return messages.pop(0)
            processed.set()
            await asyncio.sleep(10)
            return None

        fake_pubsub = MagicMock()
        fake_pubsub.psubscribe = AsyncMock()
        fake_pubsub.aclose = AsyncMock()
        fake_pubsub.get_message = fake_get_message
        fake_redis = MagicMock()
        fake_redis.pubsub = MagicMock(return_value=fake_pubsub)

        with (
            patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis),
            patch.object(mgr, "_local_broadcast", new_callable=AsyncMock) as broadcast,
        ):
            task = asyncio.create_task(mgr._redis_subscriber_loop())
            await asyncio.wait_for(processed.wait(), timeout=1.0)
            task.cancel()
            # La boucle propage desormais l'annulation, comme le veut asyncio.
            with contextlib.suppress(asyncio.CancelledError):
                await task

        broadcast.assert_awaited_with("phenomenon", {"event_type": "test"})

    @pytest.mark.asyncio
    async def should_skip_non_pmessage_types(self) -> None:
        mgr = ConnectionManager()
        processed = asyncio.Event()

        messages = [
            {"type": "subscribe", "channel": b"gsie:ws:phenomenon", "data": b"1"},
            {"type": "pmessage", "channel": "gsie:ws:alert", "data": '{"event_type":"alert"}'},
        ]

        async def fake_get_message(timeout=None):
            if messages:
                return messages.pop(0)
            processed.set()
            await asyncio.sleep(10)
            return None

        fake_pubsub = MagicMock()
        fake_pubsub.psubscribe = AsyncMock()
        fake_pubsub.aclose = AsyncMock()
        fake_pubsub.get_message = fake_get_message
        fake_redis = MagicMock()
        fake_redis.pubsub = MagicMock(return_value=fake_pubsub)

        with (
            patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis),
            patch.object(mgr, "_local_broadcast", new_callable=AsyncMock) as broadcast,
        ):
            task = asyncio.create_task(mgr._redis_subscriber_loop())
            await asyncio.wait_for(processed.wait(), timeout=1.0)
            task.cancel()
            # La boucle propage desormais l'annulation, comme le veut asyncio.
            with contextlib.suppress(asyncio.CancelledError):
                await task

        broadcast.assert_awaited_once_with("alert", {"event_type": "alert"})

    @pytest.mark.asyncio
    async def should_handle_invalid_json_in_redis_message(self) -> None:
        mgr = ConnectionManager()
        processed = asyncio.Event()

        messages = [{"type": "pmessage", "channel": b"gsie:ws:bad", "data": b"not-json"}]

        async def fake_get_message(timeout=None):
            if messages:
                return messages.pop(0)
            processed.set()
            await asyncio.sleep(10)
            return None

        fake_pubsub = MagicMock()
        fake_pubsub.psubscribe = AsyncMock()
        fake_pubsub.aclose = AsyncMock()
        fake_pubsub.get_message = fake_get_message
        fake_redis = MagicMock()
        fake_redis.pubsub = MagicMock(return_value=fake_pubsub)

        with (
            patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis),
            patch.object(mgr, "_local_broadcast", new_callable=AsyncMock) as broadcast,
        ):
            task = asyncio.create_task(mgr._redis_subscriber_loop())
            await asyncio.wait_for(processed.wait(), timeout=1.0)
            task.cancel()
            # La boucle propage desormais l'annulation, comme le veut asyncio.
            with contextlib.suppress(asyncio.CancelledError):
                await task

        broadcast.assert_not_awaited()

    @pytest.mark.asyncio
    async def should_log_warning_on_subscriber_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un Redis durablement injoignable fait abandonner, sans boucle infinie."""
        mgr = ConnectionManager()

        fake_pubsub = MagicMock()
        fake_pubsub.psubscribe = AsyncMock(side_effect=RuntimeError("pubsub broken"))
        fake_pubsub.aclose = AsyncMock()
        fake_redis = MagicMock()
        fake_redis.pubsub = MagicMock(return_value=fake_pubsub)

        # Les reprises sont bornées : la boucle s'arrête d'elle-même après
        # _REPRISES_PUBSUB_MAX tentatives. On accélère le délai entre reprises
        # pour que le test reste instantané. Pas de wait_for (deadlock sur
        # Windows avec asyncio.sleep + wait_for, Python 3.12).
        monkeypatch.setattr(manager_module, "_DELAI_REPRISE_PUBSUB", 0.001)

        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis):
            await mgr._redis_subscriber_loop()

        assert fake_pubsub.psubscribe.await_count == manager_module._REPRISES_PUBSUB_MAX + 1


class TestConnectionManagerHeartbeat:
    """Tests du heartbeat serveur."""

    @pytest.mark.asyncio
    async def should_not_start_heartbeat_when_already_started(self) -> None:
        mgr = ConnectionManager()
        mgr._heartbeat_task = asyncio.create_task(asyncio.sleep(100))
        try:
            await mgr.start_heartbeat()
        finally:
            await mgr.shutdown()

    @pytest.mark.asyncio
    async def should_start_heartbeat_task(self) -> None:
        mgr = ConnectionManager()
        await mgr.start_heartbeat()
        assert mgr._heartbeat_task is not None
        await mgr.shutdown()
        assert mgr._heartbeat_task is None

    @pytest.mark.asyncio
    async def should_clean_dead_connections_in_heartbeat(self) -> None:
        mgr = ConnectionManager()
        dead_ws = AsyncMock()
        dead_ws.send_json.side_effect = ConnectionError("dead")

        await mgr.connect(dead_ws, ["all"], roles=["reader"])

        with patch("gsie_api.websocket.manager._settings") as mock_settings:
            mock_settings.ws_heartbeat_interval = 0.05
            task = asyncio.create_task(mgr._heartbeat_loop())
            await asyncio.sleep(0.15)
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        assert dead_ws not in mgr._connections


class TestConnectionManagerConnect:
    """Tests de connect/disconnect/update_subscriptions."""

    @pytest.mark.asyncio
    async def should_reject_connection_when_max_reached(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()

        with patch("gsie_api.websocket.manager._settings") as mock_settings:
            mock_settings.ws_max_connections = 0
            result = await mgr.connect(ws, ["all"], roles=["reader"])

        assert result is False
        ws.close.assert_awaited_once_with(code=1013)
        ws.accept.assert_not_awaited()

    @pytest.mark.asyncio
    async def should_accept_with_default_all_channel(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()

        result = await mgr.connect(ws, roles=["reader"])

        assert result is True
        ws.accept.assert_awaited_once()
        assert ws in mgr._connections
        assert mgr._connections[ws] == {"all"}

    @pytest.mark.asyncio
    async def should_accept_with_specific_channels(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()

        result = await mgr.connect(ws, ["phenomenon", "alert"], roles=["admin"])

        assert result is True
        assert mgr._connections[ws] == {"phenomenon", "alert"}

    @pytest.mark.asyncio
    async def should_disconnect_and_remove_from_channels(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()

        await mgr.connect(ws, ["phenomenon", "alert"], roles=["reader"])
        await mgr.disconnect(ws)

        assert ws not in mgr._connections
        assert ws not in mgr._channels["phenomenon"]
        assert ws not in mgr._channels["alert"]

    @pytest.mark.asyncio
    async def should_disconnect_unknown_websocket_without_error(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()

        await mgr.disconnect(ws)
        assert ws not in mgr._connections

    def should_update_subscriptions_adding_new_channels(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        mgr._connections[ws] = {"phenomenon"}
        mgr._channels["phenomenon"].add(ws)

        mgr.update_subscriptions(ws, ["phenomenon", "alert"])

        assert mgr._connections[ws] == {"phenomenon", "alert"}
        assert ws in mgr._channels["alert"]

    def should_update_subscriptions_removing_old_channels(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        mgr._connections[ws] = {"phenomenon", "alert"}
        mgr._channels["phenomenon"].add(ws)
        mgr._channels["alert"].add(ws)

        mgr.update_subscriptions(ws, ["phenomenon"])

        assert mgr._connections[ws] == {"phenomenon"}
        assert ws not in mgr._channels["alert"]

    def should_can_receive_non_rgpd_channel_always(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        mgr._roles[ws] = frozenset({"reader"})

        assert mgr._can_receive(ws, "phenomenon") is True

    def should_can_receive_rgpd_channel_with_admin(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        mgr._roles[ws] = frozenset({"admin"})

        assert mgr._can_receive(ws, "consent") is True

    def should_not_can_receive_rgpd_channel_without_admin(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        mgr._roles[ws] = frozenset({"reader"})

        assert mgr._can_receive(ws, "consent") is False


class TestConnectionManagerBroadcast:
    """Tests de broadcast local et Redis."""

    @pytest.mark.asyncio
    async def should_local_broadcast_to_subscribers(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        await mgr.connect(ws, ["phenomenon"], roles=["reader"])

        await mgr._local_broadcast("phenomenon", {"event_type": "test"})

        ws.send_json.assert_awaited_with({"event_type": "test"})
        await mgr.disconnect(ws)

    @pytest.mark.asyncio
    async def should_local_broadcast_to_all_subscribers(self) -> None:
        mgr = ConnectionManager()
        ws_specific = AsyncMock()
        ws_all = AsyncMock()
        await mgr.connect(ws_specific, ["phenomenon"], roles=["reader"])
        await mgr.connect(ws_all, ["all"], roles=["reader"])

        await mgr._local_broadcast("phenomenon", {"event_type": "test"})

        ws_specific.send_json.assert_awaited_with({"event_type": "test"})
        ws_all.send_json.assert_awaited_with({"event_type": "test"})
        await mgr.disconnect(ws_specific)
        await mgr.disconnect(ws_all)

    @pytest.mark.asyncio
    async def should_disconnect_websocket_on_send_failure(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        ws.send_json.side_effect = ConnectionError("broken")
        await mgr.connect(ws, ["phenomenon"], roles=["reader"])

        await mgr._local_broadcast("phenomenon", {"event_type": "test"})

        assert ws not in mgr._connections

    @pytest.mark.asyncio
    async def should_broadcast_with_redis_publish(self) -> None:
        mgr = ConnectionManager()
        fake_redis = AsyncMock()
        ws = AsyncMock()
        await mgr.connect(ws, ["phenomenon"], roles=["reader"])

        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis):
            await mgr.broadcast("phenomenon", {"event_type": "test"})

        fake_redis.publish.assert_awaited_once()
        await mgr.disconnect(ws)

    @pytest.mark.asyncio
    async def should_broadcast_without_redis_silently(self) -> None:
        mgr = ConnectionManager()

        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=None):
            await mgr.broadcast("phenomenon", {"event_type": "test"})

    @pytest.mark.asyncio
    async def should_raise_when_require_redis_and_unavailable(self) -> None:
        mgr = ConnectionManager()

        with (
            patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=None),
            pytest.raises(RuntimeError, match="Redis unavailable"),
        ):
            await mgr.broadcast("phenomenon", {"event_type": "test"}, require_redis=True)

    @pytest.mark.asyncio
    async def should_raise_when_require_redis_and_publish_fails(self) -> None:
        mgr = ConnectionManager()
        fake_redis = AsyncMock()
        fake_redis.publish.side_effect = ConnectionError("redis down")

        with (
            patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis),
            pytest.raises(ConnectionError, match="redis down"),
        ):
            await mgr.broadcast("phenomenon", {"event_type": "test"}, require_redis=True)

    @pytest.mark.asyncio
    async def should_not_raise_when_redis_publish_fails_without_require(self) -> None:
        mgr = ConnectionManager()
        fake_redis = AsyncMock()
        fake_redis.publish.side_effect = ConnectionError("redis down")

        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=fake_redis):
            await mgr.broadcast("phenomenon", {"event_type": "test"})

    @pytest.mark.asyncio
    async def should_broadcast_event_and_log(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        await mgr.connect(ws, ["phenomenon"], roles=["reader"])

        with patch.object(mgr, "_get_redis", new_callable=AsyncMock, return_value=None):
            await mgr.broadcast_event("phenomenon", {"event_type": "phenomenon.detected"})

        ws.send_json.assert_awaited_with({"event_type": "phenomenon.detected"})
        await mgr.disconnect(ws)

    @pytest.mark.asyncio
    async def should_shutdown_and_cancel_tasks(self) -> None:
        mgr = ConnectionManager()

        async def long_task() -> None:
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                raise

        mgr._pubsub_task = asyncio.create_task(long_task())
        mgr._heartbeat_task = asyncio.create_task(long_task())

        await mgr.shutdown()

        assert mgr._pubsub_task is None
        assert mgr._heartbeat_task is None

    @pytest.mark.asyncio
    async def should_shutdown_without_tasks(self) -> None:
        mgr = ConnectionManager()
        await mgr.shutdown()
        assert mgr._pubsub_task is None
        assert mgr._heartbeat_task is None


# =====================================================================
# WebSocket Router -- endpoints /hub et /events
# =====================================================================


class TestWebSocketRouterHub:
    """Tests de l'endpoint /ws/hub via TestClient."""

    def should_connect_and_receive_pong_on_ping_text(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/hub?token={token}") as ws:
            ws.send_text("ping")
            data = ws.receive_json()
        assert data["event_type"] == "pong"

    def should_connect_and_receive_pong_on_ping_command(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/hub?token={token}") as ws:
            ws.send_text(json.dumps({"command": "ping"}))
            data = ws.receive_json()
        assert data["event_type"] == "pong"

    def should_subscribe_to_new_channels_via_command(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/hub?token={token}&channels=observation") as ws:
            ws.send_text(json.dumps({"command": "subscribe", "channels": ["alert", "phenomenon"]}))
            data = ws.receive_json()
        assert data["event_type"] == "subscribed"
        assert "alert" in data["channels"]
        assert "phenomenon" in data["channels"]

    def should_ignore_invalid_json_without_ping(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/hub?token={token}") as ws:
            ws.send_text("not-json-not-ping")
            ws.send_text("ping")
            data = ws.receive_json()
        assert data["event_type"] == "pong"

    def should_reject_connection_without_token(self) -> None:
        client = TestClient(create_app())

        with pytest.raises(WebSocketDisconnect) as exc, client.websocket_connect("/api/v1/ws/hub"):
            pass
        assert exc.value.code == 1008

    def should_reject_connection_with_invalid_token(self) -> None:
        client = TestClient(create_app())

        with (
            pytest.raises(WebSocketDisconnect) as exc,
            client.websocket_connect("/api/v1/ws/hub?token=invalid.jwt.token"),
        ):
            pass
        assert exc.value.code == 1008

    def should_rate_limit_after_max_messages(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/hub?token={token}") as ws:
            for _ in range(11):
                ws.send_text("ping")
            responses = [ws.receive_json() for _ in range(11)]

        rate_limited = [r for r in responses if r["event_type"] == "rate_limited"]
        assert len(rate_limited) >= 1


class TestWebSocketRouterEvents:
    """Tests de l'endpoint /ws/events."""

    def should_connect_and_receive_pong(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/events?token={token}") as ws:
            ws.send_text("ping")
            data = ws.receive_json()
        assert data["event_type"] == "pong"

    def should_reject_events_without_token(self) -> None:
        client = TestClient(create_app())

        with (
            pytest.raises(WebSocketDisconnect) as exc,
            client.websocket_connect("/api/v1/ws/events"),
        ):
            pass
        assert exc.value.code == 1008

    def should_rate_limit_events_endpoint(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/events?token={token}") as ws:
            for _ in range(11):
                ws.send_text("ping")
            responses = [ws.receive_json() for _ in range(11)]

        rate_limited = [r for r in responses if r["event_type"] == "rate_limited"]
        assert len(rate_limited) >= 1


class TestWebSocketRouterOrigin:
    """Tests de la politique Origin."""

    def should_allow_dev_wildcard_without_origin_header(self, monkeypatch) -> None:
        from gsie_api.websocket import router as ws_router

        monkeypatch.setattr(ws_router._settings, "ws_allowed_origins", ["*"])
        monkeypatch.setattr(ws_router._settings, "environment", "development")

        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(f"/api/v1/ws/hub?token={token}") as ws:
            ws.send_text("ping")
            data = ws.receive_json()
        assert data["event_type"] == "pong"

    def should_reject_wildcard_origin_in_non_dev(self, monkeypatch) -> None:
        from gsie_api.websocket import router as ws_router

        monkeypatch.setattr(ws_router._settings, "ws_allowed_origins", ["*"])
        monkeypatch.setattr(ws_router._settings, "environment", "staging")

        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with (
            pytest.raises(WebSocketDisconnect) as exc,
            client.websocket_connect(
                f"/api/v1/ws/hub?token={token}",
                headers={"Origin": "https://hub.example"},
            ),
        ):
            pass
        assert exc.value.code == 1008

    def should_allow_trusted_origin(self, monkeypatch) -> None:
        from gsie_api.websocket import router as ws_router

        monkeypatch.setattr(
            ws_router._settings, "ws_allowed_origins", ["https://hub.geosylva.example"]
        )

        client = TestClient(create_app())
        token = create_access_token("reader", claims={"roles": ["reader"]})

        with client.websocket_connect(
            f"/api/v1/ws/hub?token={token}",
            headers={"Origin": "https://hub.geosylva.example"},
        ) as ws:
            ws.send_text("ping")
            data = ws.receive_json()
        assert data["event_type"] == "pong"


class TestBroadcastTestEndpoint:
    """Tests complementaires de l'endpoint POST /ws/broadcast-test."""

    def should_return_success_false_for_invalid_channel(self) -> None:
        client = TestClient(create_app())
        token = create_access_token("admin", claims={"roles": ["admin"]})

        response = client.post(
            "/api/v1/ws/broadcast-test",
            json={"channel": "hacked", "message": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert body["subscribers"] == 0

    def should_return_success_true_for_valid_channel(self, monkeypatch) -> None:
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
        body = response.json()
        assert body["success"] is True
        broadcast.assert_awaited_once()


# =====================================================================
# Object Storage -- LocalStorage CRUD + S3Storage + factory
# =====================================================================


class TestLocalStorage:
    """Tests du stockage filesystem local."""

    @pytest.mark.asyncio
    async def should_put_and_return_file_uri(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        uri = await storage.put("test.txt", BytesIO(b"hello"), "text/plain")
        assert uri.startswith("file://")
        assert "test.txt" in uri

    @pytest.mark.asyncio
    async def should_get_stored_object(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        await storage.put("data.bin", BytesIO(b"content"))
        result = await storage.get("data.bin")
        assert result.read() == b"content"

    @pytest.mark.asyncio
    async def should_delete_existing_object(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        await storage.put("to_delete.txt", BytesIO(b"data"))
        deleted = await storage.delete("to_delete.txt")
        assert deleted is True
        assert await storage.exists("to_delete.txt") is False

    @pytest.mark.asyncio
    async def should_return_false_when_deleting_nonexistent(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        deleted = await storage.delete("nonexistent.txt")
        assert deleted is False

    @pytest.mark.asyncio
    async def should_check_existence(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        assert await storage.exists("missing.txt") is False
        await storage.put("found.txt", BytesIO(b"data"))
        assert await storage.exists("found.txt") is True

    @pytest.mark.asyncio
    async def should_return_presigned_url_in_local(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        url = await storage.get_presigned_url("doc.pdf", expires_in=600)
        assert url.startswith("file://")
        assert "doc.pdf" in url

    @pytest.mark.asyncio
    async def should_reject_empty_key(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        with pytest.raises(ValueError, match="Invalid object key"):
            await storage.put("", BytesIO(b"data"))

    @pytest.mark.asyncio
    async def should_reject_null_byte_in_key(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        with pytest.raises(ValueError, match="Invalid object key"):
            await storage.put("bad\x00key", BytesIO(b"data"))

    @pytest.mark.asyncio
    async def should_reject_key_resolving_to_base(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        with pytest.raises(ValueError, match="outside"):
            await storage.put(".", BytesIO(b"data"))

    @pytest.mark.asyncio
    async def should_put_in_nested_directory(self, tmp_path) -> None:
        from gsie_api.infrastructure.object_storage import LocalStorage

        storage = LocalStorage(str(tmp_path / "objects"))
        uri = await storage.put("nested/dir/file.txt", BytesIO(b"deep"))
        assert "file.txt" in uri
        assert await storage.exists("nested/dir/file.txt") is True


class TestS3Storage:
    """Tests du stockage S3 (NonImplementedError)."""

    def should_raise_not_implemented_on_init(self) -> None:
        from gsie_api.infrastructure.object_storage import S3Storage

        with pytest.raises(NotImplementedError, match="Vague 2"):
            S3Storage("http://minio:9000", "key", "secret", "bucket")


class TestObjectStorageFactory:
    """Tests de la factory get_object_storage."""

    def should_return_local_storage_in_development(self) -> None:
        from gsie_api.infrastructure import object_storage

        storage = object_storage.get_object_storage()
        assert hasattr(storage, "put")
        assert hasattr(storage, "get")


# =====================================================================
# Refresh Tokens -- Memory + Redis store
# =====================================================================


class TestMemoryRefreshTokenStore:
    """Tests du registre memoire."""

    @pytest.mark.asyncio
    async def should_register_and_consume_valid_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        jti = str(uuid4())
        expires_at = datetime.now(UTC).timestamp() + 3600

        await store.register(jti, expires_at)
        consumed = await store.consume(jti)
        assert consumed is True

    @pytest.mark.asyncio
    async def should_not_consume_already_consumed_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        jti = str(uuid4())
        expires_at = datetime.now(UTC).timestamp() + 3600

        await store.register(jti, expires_at)
        await store.consume(jti)
        second = await store.consume(jti)
        assert second is False

    @pytest.mark.asyncio
    async def should_not_consume_expired_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        jti = str(uuid4())
        expires_at = datetime.now(UTC).timestamp() - 100

        await store.register(jti, expires_at)
        consumed = await store.consume(jti)
        assert consumed is False

    @pytest.mark.asyncio
    async def should_not_consume_absent_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        consumed = await store.consume("nonexistent-jti")
        assert consumed is False

    @pytest.mark.asyncio
    async def should_rotate_valid_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        current_jti = str(uuid4())
        new_jti = str(uuid4())
        expires_at = datetime.now(UTC).timestamp() + 3600

        await store.register(current_jti, expires_at)
        rotated = await store.rotate(current_jti, new_jti, expires_at)
        assert rotated is True

        assert await store.consume(current_jti) is False
        assert await store.consume(new_jti) is True

    @pytest.mark.asyncio
    async def should_not_rotate_expired_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        current_jti = str(uuid4())
        new_jti = str(uuid4())
        expired = datetime.now(UTC).timestamp() - 100

        await store.register(current_jti, expired)
        rotated = await store.rotate(current_jti, new_jti, datetime.now(UTC).timestamp() + 3600)
        assert rotated is False

    @pytest.mark.asyncio
    async def should_not_rotate_absent_token(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        rotated = await store.rotate("absent", "new", datetime.now(UTC).timestamp() + 3600)
        assert rotated is False

    @pytest.mark.asyncio
    async def should_raise_on_collision_during_rotate(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        jti1 = str(uuid4())
        jti2 = str(uuid4())
        expires_at = datetime.now(UTC).timestamp() + 3600

        await store.register(jti1, expires_at)
        await store.register(jti2, expires_at)

        with pytest.raises(RuntimeError, match="collision"):
            await store.rotate(jti1, jti2, expires_at)

    @pytest.mark.asyncio
    async def should_close_without_error(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        await store.close()

    @pytest.mark.asyncio
    async def should_purge_expired_tokens_on_register(self) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore

        store = MemoryRefreshTokenStore()
        expired_jti = str(uuid4())
        await store.register(expired_jti, datetime.now(UTC).timestamp() - 100)

        await store.register(str(uuid4()), datetime.now(UTC).timestamp() + 3600)
        assert expired_jti not in store._tokens


class TestRedisRefreshTokenStore:
    """Tests du registre Redis avec mock."""

    @pytest.mark.asyncio
    async def should_register_token_in_redis(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.set = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            jti = str(uuid4())
            await store.register(jti, datetime.now(UTC).timestamp() + 3600)

            mock_client.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def should_raise_on_collision_in_redis(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.set = AsyncMock(return_value=False)
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            with pytest.raises(RuntimeError, match="collision"):
                await store.register("jti", datetime.now(UTC).timestamp() + 3600)

    @pytest.mark.asyncio
    async def should_consume_active_token_in_redis(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.getdel = AsyncMock(return_value="active")
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            consumed = await store.consume("jti")
            assert consumed is True

    @pytest.mark.asyncio
    async def should_not_consume_inactive_token_in_redis(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.getdel = AsyncMock(return_value=None)
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            consumed = await store.consume("jti")
            assert consumed is False

    @pytest.mark.asyncio
    async def should_rotate_successfully_in_redis(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.eval = AsyncMock(return_value=1)
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            rotated = await store.rotate("current", "new", datetime.now(UTC).timestamp() + 3600)
            assert rotated is True

    @pytest.mark.asyncio
    async def should_not_rotate_when_current_absent_in_redis(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.eval = AsyncMock(return_value=0)
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            rotated = await store.rotate("current", "new", datetime.now(UTC).timestamp() + 3600)
            assert rotated is False

    @pytest.mark.asyncio
    async def should_raise_on_collision_during_redis_rotate(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.eval = AsyncMock(return_value=-1)
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            with pytest.raises(RuntimeError, match="collision"):
                await store.rotate("current", "new", datetime.now(UTC).timestamp() + 3600)

    @pytest.mark.asyncio
    async def should_close_redis_connection(self) -> None:
        from gsie_api.auth.refresh_tokens import RedisRefreshTokenStore

        with patch("gsie_api.auth.refresh_tokens.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            store = RedisRefreshTokenStore("redis://localhost:6379/0")
            await store.close()
            mock_client.aclose.assert_awaited_once()


class TestRefreshTokenStoreFactory:
    """Tests de la factory get_refresh_token_store."""

    def should_return_memory_store_when_url_is_memory(self) -> None:
        from gsie_api.auth import refresh_tokens

        refresh_tokens.get_refresh_token_store.cache_clear()
        with patch.object(refresh_tokens, "get_settings") as mock_settings:
            mock_settings.return_value.refresh_token_storage_url = "memory://"
            store = refresh_tokens.get_refresh_token_store()
        assert hasattr(store, "register")
        refresh_tokens.get_refresh_token_store.cache_clear()

    def should_return_redis_store_when_url_is_redis(self) -> None:
        from gsie_api.auth import refresh_tokens

        refresh_tokens.get_refresh_token_store.cache_clear()
        with (
            patch.object(refresh_tokens, "get_settings") as mock_settings,
            patch("gsie_api.auth.refresh_tokens.redis.from_url"),
        ):
            mock_settings.return_value.refresh_token_storage_url = "redis://localhost:6379/0"
            store = refresh_tokens.get_refresh_token_store()
        assert hasattr(store, "register")
        refresh_tokens.get_refresh_token_store.cache_clear()

    @pytest.mark.asyncio
    async def should_close_and_clear_cache_on_close(self) -> None:
        from gsie_api.auth import refresh_tokens

        refresh_tokens.get_refresh_token_store.cache_clear()
        with patch.object(refresh_tokens, "get_settings") as mock_settings:
            mock_settings.return_value.refresh_token_storage_url = "memory://"
            await refresh_tokens.close_refresh_token_store()
        refresh_tokens.get_refresh_token_store.cache_clear()


# =====================================================================
# DPClim Client -- client HTTP Météo-France
# =====================================================================


class TestDPClimClientApiKey:
    """Tests de la validation de clé API."""

    @pytest.mark.asyncio
    async def should_raise_when_api_key_absent(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = None
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="METEOFRANCE_API_KEY"):
            await client.list_stations("75")

    @pytest.mark.asyncio
    async def should_raise_when_api_key_empty(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = ""
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="METEOFRANCE_API_KEY"):
            client._require_api_key()


class TestDPClimClientListStations:
    """Tests de list_stations avec respx."""

    @pytest.mark.asyncio
    @respx.mock
    async def should_list_stations_successfully(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient

        stations = [{"id": "1", "nom": "Paris-Montsouris"}, {"id": "2", "nom": "Orly"}]
        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/liste-stations/quotidienne",
            params={"id-departement": "75"},
        ).respond(200, json=stations)

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient()
        result = await client.list_stations("75")
        assert result == stations

    @pytest.mark.asyncio
    @respx.mock
    async def should_raise_on_http_error_list_stations(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/liste-stations/quotidienne",
            params={"id-departement": "75"},
        ).respond(500)

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="liste-stations"):
            await client.list_stations("75")


class TestDPClimClientGetDonnees:
    """Tests du flux complet commande + polling."""

    @pytest.mark.asyncio
    @respx.mock
    async def should_get_donnees_quotidiennes_successfully(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient

        commande_route = respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(
            200,
            json={"elaboreProduitAvecDemandeResponse": {"return": "cmd-123"}},
        )
        fichier_route = respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier",
        ).respond(200, text="NOM_POSTE;RR\nParis;1.5\n")

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient(poll_interval_s=0.01, max_poll_attempts=3)
        result = await client.get_donnees_quotidiennes(
            "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
        )

        assert "Paris" in result
        assert commande_route.called
        assert fichier_route.called

    @pytest.mark.asyncio
    async def should_raise_when_no_api_key_for_donnees(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = None
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="METEOFRANCE_API_KEY"):
            await client.get_donnees_quotidiennes(
                "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
            )

    @pytest.mark.asyncio
    @respx.mock
    async def should_poll_until_ready_then_succeed(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(200, json={"elaboreProduitAvecDemandeResponse": {"return": "cmd-456"}})

        fichier_route = respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier",
        )
        fichier_route.side_effect = [
            httpx.Response(404, text="not ready"),
            httpx.Response(404, text="not ready"),
            httpx.Response(200, text="NOM_POSTE;RR\nOrly;2.0\n"),
        ]

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient(poll_interval_s=0.01, max_poll_attempts=5)
        result = await client.get_donnees_quotidiennes(
            "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
        )

        assert "Orly" in result
        assert fichier_route.call_count == 3

    @pytest.mark.asyncio
    @respx.mock
    async def should_raise_when_commande_never_ready(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(200, json={"elaboreProduitAvecDemandeResponse": {"return": "cmd-789"}})

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier",
        ).respond(404, text="not ready")

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient(poll_interval_s=0.01, max_poll_attempts=2)
        with pytest.raises(DPClimClientError, match="DPClim"):
            await client.get_donnees_quotidiennes(
                "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
            )

    @pytest.mark.asyncio
    @respx.mock
    async def should_raise_on_500_during_fichier_fetch(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(200, json={"elaboreProduitAvecDemandeResponse": {"return": "cmd-500"}})

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier",
        ).respond(500, text="server error")

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient(poll_interval_s=0.01, max_poll_attempts=3)
        with pytest.raises(DPClimClientError, match="commande/fichier"):
            await client.get_donnees_quotidiennes(
                "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
            )

    @pytest.mark.asyncio
    @respx.mock
    async def should_raise_on_commande_http_error(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(500)

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="commande-station"):
            await client.get_donnees_quotidiennes(
                "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
            )

    @pytest.mark.asyncio
    @respx.mock
    async def should_raise_on_commande_invalid_json(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(200, text="not-json-at-all")

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="illisible"):
            await client.get_donnees_quotidiennes(
                "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
            )

    @pytest.mark.asyncio
    @respx.mock
    async def should_raise_on_commande_missing_return_key(self) -> None:
        from gsie_api.engines.climate.dpclim_client import DPClimClient, DPClimClientError

        respx.get(
            "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne",
        ).respond(200, json={"unexpected": "structure"})

        with patch("gsie_api.engines.climate.dpclim_client.get_settings") as mock:
            mock.return_value.meteofrance_api_key = "test-key"
            client = DPClimClient()
        with pytest.raises(DPClimClientError, match="commande-station"):
            await client.get_donnees_quotidiennes(
                "75056", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
            )


# =====================================================================
# Run Seeds -- refus explicite du seed v6.1
# =====================================================================


class TestRunSeeds:
    """Tests du point d'entree des seeds v6.1 (retire)."""

    @pytest.mark.asyncio
    async def should_raise_runtime_error_when_run_seeds_called(self) -> None:
        from gsie_api.seeds.run_seeds import run_seeds

        with pytest.raises(RuntimeError, match="DEC-000023"):
            await run_seeds()

    @pytest.mark.asyncio
    async def should_raise_regardless_of_flags(self) -> None:
        from gsie_api.seeds.run_seeds import run_seeds

        with pytest.raises(RuntimeError, match="DEC-000023"):
            await run_seeds(botanical=True, ecosystem=False)
        with pytest.raises(RuntimeError, match="DEC-000023"):
            await run_seeds(botanical=False, ecosystem=True)

    def should_main_raises_runtime_error_via_cli(self) -> None:
        from gsie_api.seeds import run_seeds

        with (
            patch("sys.argv", ["run_seeds"]),
            pytest.raises(RuntimeError, match="DEC-000023"),
        ):
            run_seeds.main()

    def should_main_with_botanical_only_flag_raises(self) -> None:
        from gsie_api.seeds import run_seeds

        with (
            patch("sys.argv", ["run_seeds", "--botanical-only"]),
            pytest.raises(RuntimeError, match="DEC-000023"),
        ):
            run_seeds.main()

    def should_main_with_ecosystem_only_flag_raises(self) -> None:
        from gsie_api.seeds import run_seeds

        with (
            patch("sys.argv", ["run_seeds", "--ecosystem-only"]),
            pytest.raises(RuntimeError, match="DEC-000023"),
        ):
            run_seeds.main()


# =====================================================================
# Outbox Worker -- run_worker, main, _publish_to_redis, edge cases
# =====================================================================


class TestOutboxWorkerPublishToRedis:
    """Tests du publisher Redis par defaut."""

    @pytest.mark.asyncio
    async def should_publish_to_redis_via_ws_manager(self) -> None:
        from gsie_api.outbox_worker import _publish_to_redis

        with patch(
            "gsie_api.outbox_worker.ws_manager.broadcast_event",
            new_callable=AsyncMock,
        ) as mock_broadcast:
            await _publish_to_redis("entity", {"event_id": "test"})
        mock_broadcast.assert_awaited_once_with("entity", {"event_id": "test"}, require_redis=True)


class TestOutboxWorkerRetryPolicy:
    """Tests de RetryPolicy.from_settings."""

    def should_build_policy_from_settings(self) -> None:
        from gsie_api.outbox_worker import RetryPolicy

        policy = RetryPolicy.from_settings()
        assert policy.max_attempts > 0
        assert policy.base_seconds > 0
        assert policy.max_seconds > 0

    def should_is_exhausted_when_attempt_reaches_max(self) -> None:
        from gsie_api.outbox_worker import RetryPolicy

        policy = RetryPolicy(max_attempts=3, base_seconds=1.0, max_seconds=10.0, jitter_ratio=0.0)
        assert policy.is_exhausted(3) is True
        assert policy.is_exhausted(2) is False


class TestOutboxWorkerRequeueEdgeCases:
    """Tests des cas limites du re-enfilement."""

    @pytest.mark.asyncio
    async def should_return_zero_when_event_ids_empty_list(self) -> None:
        from gsie_api.outbox_worker import requeue_dead_letters

        session = AsyncMock()
        result = await requeue_dead_letters(session, event_ids=[], reason="test")
        assert result == 0
        session.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def should_requeue_with_limit_only(self) -> None:
        from gsie_api.infrastructure.models.outbox import OutboxEvent
        from gsie_api.outbox_worker import requeue_dead_letters

        event_id = uuid4()
        fake_event = OutboxEvent(
            id=event_id,
            aggregate_id=uuid4(),
            aggregate_type="entity",
            event_type="resource.created",
            payload={"event_id": str(event_id)},
            created_at=datetime.now(UTC),
            status="dead_letter",
            attempt_count=3,
            next_attempt_at=datetime.now(UTC),
        )

        session = AsyncMock()
        scalars = MagicMock()
        scalars.all.return_value = [fake_event]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars
        session.execute = AsyncMock(return_value=result_mock)

        result = await requeue_dead_letters(
            session, limit=10, reason="incident resolu", clock=lambda: datetime.now(UTC)
        )
        assert result == 1
        assert fake_event.status == "pending"
        assert fake_event.attempt_count == 0
        session.commit.assert_awaited_once()


class TestOutboxWorkerRunWorker:
    """Tests de la boucle run_worker avec mock de session."""

    @pytest.mark.asyncio
    async def should_process_batch_and_sleep_when_empty(self) -> None:
        from gsie_api.outbox_worker import run_worker

        session = AsyncMock()
        session_factory = MagicMock()
        session_factory.__aenter__ = AsyncMock(return_value=session)
        session_factory.__aexit__ = AsyncMock(return_value=None)

        call_count = 0

        async def fake_deliver(session, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError()
            return 0

        with (
            patch("gsie_api.outbox_worker.async_session_factory", return_value=session_factory),
            patch("gsie_api.outbox_worker.deliver_outbox_batch", side_effect=fake_deliver),
            patch("gsie_api.outbox_worker.collect_outbox_stats", new_callable=AsyncMock),
            patch("gsie_api.outbox_worker.setup_logging"),
            patch("gsie_api.outbox_worker.asyncio.sleep", new_callable=AsyncMock),
            patch("gsie_api.outbox_worker.ws_manager.shutdown", new_callable=AsyncMock),
            pytest.raises(asyncio.CancelledError),
        ):
            await run_worker()

    @pytest.mark.asyncio
    async def should_rollback_on_exception_and_continue(self) -> None:
        from gsie_api.outbox_worker import run_worker

        session = AsyncMock()
        session_factory = MagicMock()
        session_factory.__aenter__ = AsyncMock(return_value=session)
        session_factory.__aexit__ = AsyncMock(return_value=None)

        call_count = 0

        async def fake_deliver(session, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("db error")
            raise asyncio.CancelledError()

        with (
            patch("gsie_api.outbox_worker.async_session_factory", return_value=session_factory),
            patch("gsie_api.outbox_worker.deliver_outbox_batch", side_effect=fake_deliver),
            patch("gsie_api.outbox_worker.setup_logging"),
            patch("gsie_api.outbox_worker.asyncio.sleep", new_callable=AsyncMock),
            patch("gsie_api.outbox_worker.ws_manager.shutdown", new_callable=AsyncMock),
            pytest.raises(asyncio.CancelledError),
        ):
            await run_worker()

        session.rollback.assert_awaited()

    @pytest.mark.asyncio
    async def should_rollback_and_reraise_on_cancelled_error(self) -> None:
        from gsie_api.outbox_worker import run_worker

        session = AsyncMock()
        session_factory = MagicMock()
        session_factory.__aenter__ = AsyncMock(return_value=session)
        session_factory.__aexit__ = AsyncMock(return_value=None)

        async def fake_deliver(session, **kwargs):
            raise asyncio.CancelledError()

        with (
            patch("gsie_api.outbox_worker.async_session_factory", return_value=session_factory),
            patch("gsie_api.outbox_worker.deliver_outbox_batch", side_effect=fake_deliver),
            patch("gsie_api.outbox_worker.setup_logging"),
            patch("gsie_api.outbox_worker.ws_manager.shutdown", new_callable=AsyncMock),
            pytest.raises(asyncio.CancelledError),
        ):
            await run_worker()

        session.rollback.assert_awaited()


class TestOutboxWorkerMain:
    """Tests du point d'entree main()."""

    def should_run_worker_via_main(self) -> None:
        from gsie_api.outbox_worker import main

        with (
            patch("gsie_api.outbox_worker.run_worker", new_callable=AsyncMock),
            patch("gsie_api.outbox_worker.asyncio.run") as mock_run,
        ):
            main()
        mock_run.assert_called_once()

    def should_suppress_keyboard_interrupt_in_main(self) -> None:
        from gsie_api.outbox_worker import main

        with patch("gsie_api.outbox_worker.asyncio.run", side_effect=KeyboardInterrupt):
            main()


class TestOutboxWorkerCodeErreur:
    """Tests de la fonction _code_erreur."""

    def should_return_class_name_sanitized(self) -> None:
        from gsie_api.outbox_worker import _code_erreur

        assert _code_erreur(RuntimeError("test")) == "RuntimeError"
        assert _code_erreur(ConnectionError("redis://secret")) == "ConnectionError"

    def should_return_unknown_for_empty_class_name(self) -> None:
        from gsie_api.outbox_worker import _code_erreur

        empty_exc = type("", (Exception,), {})("msg")
        assert _code_erreur(empty_exc) == "UnknownError"

    def should_truncate_long_class_names(self) -> None:
        from gsie_api.outbox_worker import _code_erreur

        long_exc = type("A" * 200, (Exception,), {})("msg")
        code = _code_erreur(long_exc)
        assert len(code) <= 100
