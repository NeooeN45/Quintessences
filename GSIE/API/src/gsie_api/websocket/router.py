"""Router WebSocket — endpoints temps réel pour le Hub (UE5.8).

WS /api/v1/ws/hub     — canal temps réel Hub (Centre de Commandement)
WS /api/v1/ws/events  — events système (resource.created, etc.)

Sécurité :
- Token JWT obligatoire en query param (?token=xxx)
  Note : Le protocole WebSocket natif ne permet pas de passer des headers
  personnalisés lors du handshake (seuls les subprotocols sont supportés).
  Le token en query param est le standard de facto pour WS auth (Socket.io,
  SignalR, Action Cable). Mitigations : HTTPS en prod (token chiffré en
  transit), tokens courts (15min access), pas de log des query params par
  le middleware (configuré dans shared/middleware.py).
- Rate limiting : max 10 messages/minute par client
- Validation des canaux : canaux autorisés uniquement (16 canaux)
"""

import json
from collections import defaultdict, deque
from datetime import UTC, datetime
from time import monotonic
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from gsie_api.core.auth import verify_ws_token
from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger
from gsie_api.core.rbac import can_access_resource, get_user_roles, require_roles
from gsie_api.websocket.events import EventType, WSEvent
from gsie_api.websocket.manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])
_settings = get_settings()
logger = get_logger("gsie_api.websocket.router")

# Canaux autorisés (sécurité — pas d'abonnement arbitraire)
_ALLOWED_CHANNELS = frozenset(
    {
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
    }
)

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
_require_admin = require_roles("admin")


def _validate_channels(channels: list[str] | None) -> list[str]:
    """Valide que les canaux demandés sont autorisés."""
    if not channels:
        return ["all"]
    valid = [c for c in channels if c in _ALLOWED_CHANNELS]
    return valid if valid else ["all"]


def _is_origin_allowed(websocket: WebSocket) -> bool:
    """Applique une liste blanche Origin au handshake navigateur."""
    origin = websocket.headers.get("origin")
    allowed = _settings.ws_allowed_origins
    if origin is None:
        return _settings.environment == "development" and "*" in allowed
    if "*" in allowed:
        return _settings.environment == "development"
    return origin in allowed


async def _authenticate_ws(websocket: WebSocket) -> dict[str, Any] | None:
    """Authentifie une connexion WebSocket via token en query param."""
    if not _is_origin_allowed(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Origine interdite")
        return None
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token manquant")
        return None
    user = await verify_ws_token(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token invalide")
        return None
    if not can_access_resource(user, "engine", "read"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Rôle insuffisant")
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

    accepted = await manager.connect(websocket, validated, roles=get_user_roles(user))
    if not accepted:
        return
    ws_id = id(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if not _rate_limiter.check(ws_id):
                await websocket.send_json(
                    {
                        "event_type": "rate_limited",
                        "message": "Trop de messages. Réessayez dans 60s.",
                    }
                )
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
                await websocket.send_json(
                    {
                        "event_type": "subscribed",
                        "channels": new_channels,
                    }
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        _rate_limiter.cleanup(ws_id)


@router.websocket("/events")
async def ws_events(websocket: WebSocket) -> None:
    """Canal WebSocket pour les events système (resource.created, etc.)."""
    user = await _authenticate_ws(websocket)
    if user is None:
        return

    accepted = await manager.connect(websocket, ["all"], roles=get_user_roles(user))
    if not accepted:
        return
    ws_id = id(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if not _rate_limiter.check(ws_id):
                await websocket.send_json(
                    {
                        "event_type": "rate_limited",
                        "message": "Trop de messages. Réessayez dans 60s.",
                    }
                )
                continue
            if data == "ping":
                await websocket.send_json({"event_type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        _rate_limiter.cleanup(ws_id)


# --- Endpoint REST de test broadcast (Gate 5 — E2E) --------------------------


class BroadcastTestRequest(BaseModel):
    """Payload pour publier un event de test sur le WebSocket."""

    channel: str = "all"
    event_type: EventType = EventType.observation_received
    message: str = "Test E2E Gate 5 — Hub UE5.8"


class BroadcastTestResponse(BaseModel):
    """Réponse de l'endpoint de test broadcast."""

    success: bool
    channel: str
    event_type: str
    subscribers: int


@router.post(
    "/broadcast-test",
    response_model=BroadcastTestResponse,
    summary="Publie un event de test sur le WebSocket (admin uniquement)",
    description=(
        "Endpoint REST pour valider la chaîne E2E : "
        "API → WebSocket → Hub UE5.8. "
        "Publie un event sur le canal spécifié et retourne le nombre d'abonnés."
    ),
)
async def broadcast_test(
    payload: BroadcastTestRequest,
    _user: dict[str, Any] = Depends(_require_admin),
) -> BroadcastTestResponse:
    """Publie un event de test sur le WebSocket pour validation E2E."""
    if payload.channel not in _ALLOWED_CHANNELS:
        return BroadcastTestResponse(
            success=False,
            channel=payload.channel,
            event_type=payload.event_type.value,
            subscribers=0,
        )

    event = WSEvent(
        event_type=payload.event_type,
        data={"message": payload.message, "test_id": str(uuid4())},
        timestamp=datetime.now(UTC).isoformat(),
        trace_id=f"GATE5-E2E-{uuid4().hex[:8]}",
    )

    await manager.broadcast(payload.channel, event.model_dump(mode="json"))

    subscriber_count = len(manager._channels.get(payload.channel, set()))

    logger.info(
        "ws_broadcast_test",
        channel=payload.channel,
        event_type=payload.event_type.value,
        subscribers=subscriber_count,
    )

    return BroadcastTestResponse(
        success=True,
        channel=payload.channel,
        event_type=payload.event_type.value,
        subscribers=subscriber_count,
    )
