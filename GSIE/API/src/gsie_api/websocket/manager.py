"""ConnectionManager WebSocket — gestion des connexions + Redis Pub/Sub.

Chaque client peut s'abonner à des canaux :
- Par type de resource (ex. "phenomenon", "observation", "alert")
- Canal global "all" pour tous les events

Redis Pub/Sub assure le fan-out entre les workers Gunicorn.
"""

import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from gsie_api.core.logging import get_logger

logger = get_logger("gsie_api.websocket.manager")


class ConnectionManager:
    """Gestionnaire de connexions WebSocket avec abonnements par canal.

    In-memory pour les connexions locales + Redis Pub/Sub pour le fan-out
    inter-workers (ADR-007).
    """

    def __init__(self) -> None:
        self._connections: dict[WebSocket, set[str]] = {}
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis = None  # Initialisé lazy si Redis configuré

    async def _get_redis(self):
        """Récupère la connexion Redis (lazy init)."""
        if self._redis is None:
            try:
                from gsie_api.infrastructure.redis_client import get_redis

                self._redis = await get_redis()
            except Exception:
                logger.warning("redis_unavailable_ws_fanout_degraded", exc_info=True)
        return self._redis

    async def connect(self, websocket: WebSocket, channels: list[str] | None = None) -> None:
        """Accepte une connexion WebSocket et l'abonne à des canaux."""
        await websocket.accept()
        subs = set(channels) if channels else {"all"}
        self._connections[websocket] = subs
        for channel in subs:
            self._channels[channel].add(websocket)
        logger.info(
            "ws_connected",
            channels=list(subs),
            total_connections=len(self._connections),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Déconnecte un client et le désabonne de tous ses canaux."""
        subs = self._connections.pop(websocket, set())
        for channel in subs:
            self._channels[channel].discard(websocket)
        logger.info(
            "ws_disconnected",
            total_connections=len(self._connections),
        )

    def update_subscriptions(self, websocket: WebSocket, channels: list[str]) -> None:
        """Met à jour les abonnements d'un client connecté."""
        old_subs = self._connections.get(websocket, set())
        new_subs = set(channels)
        for channel in old_subs - new_subs:
            self._channels[channel].discard(websocket)
        for channel in new_subs - old_subs:
            self._channels[channel].add(websocket)
        self._connections[websocket] = new_subs

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Diffuse un message à tous les abonnés d'un canal (local + Redis)."""
        # 1. Diffusion locale (workers sur cette instance)
        subscribers = self._channels.get(channel, set())
        subscribers_all = self._channels.get("all", set())
        targets = subscribers | subscribers_all

        for ws in list(targets):  # copie car disconnect modifie pendant itération
            try:
                await ws.send_json(message)
            except Exception:
                logger.debug("ws_send_failed", exc_info=True)
                await self.disconnect(ws)

        # 2. Fan-out Redis pour les autres workers
        redis = await self._get_redis()
        if redis:
            try:
                await redis.publish(
                    f"gsie:ws:{channel}",
                    json.dumps(message),
                )
            except Exception:
                logger.warning("redis_publish_failed", channel=channel, exc_info=True)

    async def broadcast_event(self, channel: str, event: dict[str, Any]) -> None:
        """Diffuse un event typé sur un canal."""
        await self.broadcast(channel, event)
        logger.info(
            "ws_event_broadcast",
            channel=channel,
            event_type=event.get("event_type"),
        )


# Singleton — partagé entre les workers d'une même instance
manager = ConnectionManager()
