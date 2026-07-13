"""Redis — cache, Pub/Sub, WebSocket fan-out (DEC-000019)."""

import redis.asyncio as redis

from gsie_api.core.config import get_settings

_settings = get_settings()

# Pool de connexions Redis pour cache + Pub/Sub
# Timeouts configurés pour éviter les requêtes bloquantes (résilience P0)
redis_pool = redis.ConnectionPool.from_url(
    _settings.redis_url,
    max_connections=_settings.redis_max_connections,
    decode_responses=True,
    socket_timeout=_settings.redis_socket_timeout,
    socket_connect_timeout=_settings.redis_connect_timeout,
)


async def get_redis() -> redis.Redis:
    """Dependency FastAPI — client Redis depuis le pool."""
    return redis.Redis(connection_pool=redis_pool)
