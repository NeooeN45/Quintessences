"""ConnectionManager WebSocket — gestion des connexions + Redis Pub/Sub.

Chaque client peut s'abonner à des canaux :
- Par type de resource (ex. "phenomenon", "observation", "alert")
- Canal global "all" pour tous les events

Redis Pub/Sub assure le fan-out entre les workers Gunicorn :
- publish() diffuse les events locaux vers les autres workers
- subscribe() écoute les events des autres workers et les redistribue localement

Sécurité :
- Plafond de connexions (ws_max_connections) pour éviter l'OOM
- Heartbeat serveur (ws_heartbeat_interval) pour détecter les connexions mortes
"""

import asyncio
import json
from collections import defaultdict
from collections.abc import Collection
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger
from gsie_api.core.rbac import RGPD_RESOURCE_TYPES

logger = get_logger("gsie_api.websocket.manager")
_settings = get_settings()


class ConnectionManager:
    """Gestionnaire de connexions WebSocket avec abonnements par canal.

    In-memory pour les connexions locales + Redis Pub/Sub pour le fan-out
    inter-workers (ADR-007).
    """

    def __init__(self) -> None:
        self._connections: dict[WebSocket, set[str]] = {}
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._roles: dict[WebSocket, frozenset[str]] = {}
        self._redis: Redis | None = None
        self._pubsub_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None

    async def _get_redis(self) -> Redis | None:
        """Récupère la connexion Redis (lazy init)."""
        if self._redis is None:
            try:
                from gsie_api.infrastructure.redis_client import get_redis

                self._redis = await get_redis()
            except Exception:
                logger.warning("redis_unavailable_ws_fanout_degraded", exc_info=True)
        return self._redis

    async def start_redis_subscriber(self) -> None:
        """Démarre l'écoute Redis Pub/Sub pour le fan-out inter-workers.

        Sans cette étape, les events publiés par d'autres workers ne sont
        jamais reçus — le fan-out est à moitié fait (pub sans sub).
        """
        redis = await self._get_redis()
        if redis is None:
            return
        if self._pubsub_task is not None:
            return  # déjà démarré

        self._pubsub_task = asyncio.create_task(self._redis_subscriber_loop())
        logger.info("ws_redis_subscriber_started")

    async def _redis_subscriber_loop(self) -> None:
        """Boucle d'écoute Redis Pub/Sub — redistribue les events inter-workers."""
        redis = await self._get_redis()
        if redis is None:
            return
        try:
            pubsub = redis.pubsub()
            # S'abonner à tous les canaux gsie:ws:*
            await pubsub.psubscribe("gsie:ws:*")
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                channel = message["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode()
                # Extraire le nom du canal (gsie:ws:phenomenon → phenomenon)
                canal_name = channel.replace("gsie:ws:", "")
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                try:
                    event = json.loads(data)
                    # Diffusion locale uniquement (pas de re-publish pour éviter la boucle)
                    await self._local_broadcast(canal_name, event)
                except (json.JSONDecodeError, TypeError):
                    logger.debug("ws_redis_invalid_message", channel=canal_name)
        except asyncio.CancelledError:
            logger.info("ws_redis_subscriber_stopped")
        except Exception:
            logger.warning("ws_redis_subscriber_error", exc_info=True)

    async def start_heartbeat(self) -> None:
        """Démarre le heartbeat serveur pour détecter les connexions mortes.

        Sans heartbeat, une connexion qui meurt sans clôture propre (coupure
        réseau du Hub Unreal) reste en mémoire indéfiniment → OOM potentiel.
        """
        if self._heartbeat_task is not None:
            return
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("ws_heartbeat_started")

    async def _heartbeat_loop(self) -> None:
        """Boucle de heartbeat — ping périodique + nettoyage des connexions mortes."""
        interval = _settings.ws_heartbeat_interval
        try:
            while True:
                await asyncio.sleep(interval)
                dead: list[WebSocket] = []
                for ws in list(self._connections):
                    try:
                        await ws.send_json({"event_type": "ping"})
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    await self.disconnect(ws)
                if dead:
                    logger.info("ws_heartbeat_cleaned", cleaned=len(dead))
        except asyncio.CancelledError:
            logger.info("ws_heartbeat_stopped")

    async def connect(
        self,
        websocket: WebSocket,
        channels: list[str] | None = None,
        *,
        roles: Collection[str] = (),
    ) -> bool:
        """Accepte une connexion WebSocket et l'abonne à des canaux.

        Returns:
            True si acceptée, False si le plafond de connexions est atteint.
        """
        if len(self._connections) >= _settings.ws_max_connections:
            logger.warning(
                "ws_connection_rejected",
                total=len(self._connections),
                max=_settings.ws_max_connections,
            )
            await websocket.close(code=1013)  # Try Again Later
            return False

        await websocket.accept()
        subs = set(channels) if channels else {"all"}
        self._connections[websocket] = subs
        self._roles[websocket] = frozenset(roles)
        for channel in subs:
            self._channels[channel].add(websocket)
        logger.info(
            "ws_connected",
            channels=list(subs),
            total_connections=len(self._connections),
        )
        return True

    async def disconnect(self, websocket: WebSocket) -> None:
        """Déconnecte un client et le désabonne de tous ses canaux."""
        subs = self._connections.pop(websocket, set())
        self._roles.pop(websocket, None)
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

    def _can_receive(self, websocket: WebSocket, channel: str) -> bool:
        """Filtre les canaux RGPD même pour un abonnement global all."""
        if channel not in RGPD_RESOURCE_TYPES:
            return True
        roles = self._roles.get(websocket, frozenset())
        return bool(roles.intersection({"admin", "rgpd_manager"}))

    async def _local_broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Diffuse un message aux abonnés locaux uniquement (pas de Redis)."""
        subscribers = self._channels.get(channel, set())
        subscribers_all = self._channels.get("all", set())
        targets = subscribers | subscribers_all

        for ws in list(targets):
            if not self._can_receive(ws, channel):
                continue
            try:
                await ws.send_json(message)
            except Exception:
                logger.debug("ws_send_failed", exc_info=True)
                await self.disconnect(ws)

    async def broadcast(
        self,
        channel: str,
        message: dict[str, Any],
        *,
        require_redis: bool = False,
    ) -> None:
        """Diffuse un message à tous les abonnés d'un canal (local + Redis)."""
        # 1. Diffusion locale (workers sur cette instance)
        await self._local_broadcast(channel, message)

        # 2. Fan-out Redis pour les autres workers
        redis = await self._get_redis()
        if redis:
            try:
                await redis.publish(
                    f"gsie:ws:{channel}",
                    json.dumps(message),
                )
            except Exception:
                if require_redis:
                    raise
                logger.warning("redis_publish_failed", channel=channel, exc_info=True)
        elif require_redis:
            raise RuntimeError("Redis unavailable for required event delivery")

    async def broadcast_event(
        self,
        channel: str,
        event: dict[str, Any],
        *,
        require_redis: bool = False,
    ) -> None:
        """Diffuse un event typé sur un canal."""
        await self.broadcast(channel, event, require_redis=require_redis)
        logger.info(
            "ws_event_broadcast",
            channel=channel,
            event_type=event.get("event_type"),
        )

    async def shutdown(self) -> None:
        """Arrête proprement les tâches de fond (subscriber + heartbeat)."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            self._pubsub_task = None
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        logger.info("ws_manager_shutdown")


# Singleton — partagé entre les workers d'une même instance
manager = ConnectionManager()
