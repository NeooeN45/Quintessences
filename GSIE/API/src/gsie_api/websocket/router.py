"""Router WebSocket — endpoints temps réel pour le Hub (UE5.8).

WS /api/v1/ws/hub     — canal temps réel Hub (Centre de Commandement)
WS /api/v1/ws/events  — events système (resource.created, etc.)

Sécurité :
- Token JWT obligatoire en query param (?token=xxx)
- Rate limiting : max 10 messages/minute par client
- Validation des canaux : canaux autorisés uniquement
"""

import json
from collections import defaultdict, deque
from time import monotonic

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from gsie_api.core.auth import verify_ws_token
from gsie_api.core.logging import get_logger
from gsie_api.websocket.manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = get_logger("gsie_api.websocket.router")

# Canaux autorisés (sécurité — pas d'abonnement arbitraire)
_ALLOWED_CHANNELS = frozenset({
    "all",
    "assertion",
    "observation",
    "phenomenon",
    "alert",
    "alert.fire_risk",
    "alert.drought",
    "alert.storm",
    "alert.pest",
    "model",
    "recommendation",
    "correlation",
    "place",
    "scenario",
    "ecological_state",
})

# Rate limiting simple — 10 messages / 60s par WebSocket
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60.0


class _RateLimiter:
    """Rate limiter in-memory par WebSocket (best-effort)."""

    def __init__(self) -> None:
        self._timestamps: dict[int, deque[float]] = defaultdict(deque)

    def check(self, ws_id: int) -> bool:
        """Retourne True si le message est autorisé, False si limité."""
        now = monotonic()
        timestamps = self._timestamps[ws_id]
        while timestamps and now - timestamps[0] > _RATE_LIMIT_WINDOW:
            timestamps.popleft()
        if len(timestamps) >= _RATE_LIMIT_MAX:
            return False
        timestamps.append(now)
        return True

    def cleanup(self, ws_id: int) -> None:
        self._timestamps.pop(ws_id, None)


_rate_limiter = _RateLimiter()


def _validate_channels(channels: list[str] | None) -> list[str]:
    """Valide que les canaux demandés sont autorisés."""
    if not channels:
        return ["all"]
    valid = [c for c in channels if c in _ALLOWED_CHANNELS]
    return valid if valid else ["all"]


async def _authenticate_ws(websocket: WebSocket) -> dict | None:
    """Authentifie une connexion WebSocket via token en query param."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token manquant")
        return None
    user = await verify_ws_token(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token invalide")
        return None
    return user


@router.websocket("/hub")
async def ws_hub(
    websocket: WebSocket,
    channels: str | None = Query(default=None, description="Canaux séparés par virgule"),
) -> None:
    """Canal WebSocket temps réel pour le Hub (Unreal Engine 5.8).

    Query params :
    - token : JWT access token (obligatoire)
    - channels : canaux séparés par virgule (ex. phenomenon,alert,observation)
    """
    user = await _authenticate_ws(websocket)
    if user is None:
        return

    channel_list = channels.split(",") if channels else None
    validated = _validate_channels(channel_list)

    await manager.connect(websocket, validated)
    ws_id = id(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if not _rate_limiter.check(ws_id):
                await websocket.send_json({
                    "event_type": "rate_limited",
                    "message": "Trop de messages. Réessayez dans 60s.",
                })
                continue

            # Le Hub peut envoyer des commandes
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                if data == "ping":
                    await websocket.send_json({"event_type": "pong"})
                continue

            cmd = msg.get("command")
            if cmd == "ping":
                await websocket.send_json({"event_type": "pong"})
            elif cmd == "subscribe":
                new_channels = _validate_channels(msg.get("channels", []))
                manager.update_subscriptions(websocket, new_channels)
                await websocket.send_json({
                    "event_type": "subscribed",
                    "channels": new_channels,
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        _rate_limiter.cleanup(ws_id)


@router.websocket("/events")
async def ws_events(websocket: WebSocket) -> None:
    """Canal WebSocket pour les events système (resource.created, etc.)."""
    user = await _authenticate_ws(websocket)
    if user is None:
        return

    await manager.connect(websocket, ["all"])
    ws_id = id(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if not _rate_limiter.check(ws_id):
                await websocket.send_json({
                    "event_type": "rate_limited",
                    "message": "Trop de messages. Réessayez dans 60s.",
                })
                continue
            if data == "ping":
                await websocket.send_json({"event_type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        _rate_limiter.cleanup(ws_id)
