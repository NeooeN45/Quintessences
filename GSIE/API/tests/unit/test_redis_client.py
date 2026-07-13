"""Tests unitaires — client Redis (infrastructure/redis_client.py)."""

import redis.asyncio as redis

from gsie_api.infrastructure.redis_client import get_redis, redis_pool


def should_create_pool_with_correct_config():
    """redis_pool doit être créé avec max_connections et decode_responses."""
    assert redis_pool is not None
    assert redis_pool.max_connections is not None


def should_return_redis_client_when_get_redis_called():
    """get_redis doit retourner un client Redis connecté au pool."""
    import asyncio

    async def _test():
        client = await get_redis()
        assert isinstance(client, redis.Redis)
        assert client.connection_pool is redis_pool

    asyncio.run(_test())
