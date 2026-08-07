"""Couverture du registre de nonces OIDC génériques (miroir de google_nonces).

Voir PENTEST_AUTH_CONNEXION_2026-08-07.md §2.1 — module créé le 2026-08-07,
sans test dédié avant ce fichier.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gsie_api.auth import oidc_nonces
from gsie_api.auth.oidc_nonces import (
    MemoryOidcNonceStore,
    RedisOidcNonceStore,
    get_oidc_nonce_store,
)


async def should_create_and_consume_memory_nonce_once() -> None:
    store = MemoryOidcNonceStore(ttl_seconds=300)
    assert store.ttl_seconds == 300
    nonce = await store.create()
    assert isinstance(nonce, str)
    assert await store.consume(nonce) is True
    # Consommation à usage unique : la seconde tentative échoue.
    assert await store.consume(nonce) is False


async def should_reject_unknown_memory_nonce() -> None:
    store = MemoryOidcNonceStore()
    assert await store.consume("inconnu") is False


async def should_cover_memory_nonce_expiry_and_close() -> None:
    store = MemoryOidcNonceStore(ttl_seconds=1)
    assert store.ttl_seconds == 1
    store._nonces["expire"] = 0  # noqa: SLF001 - horloge déterministe du test
    await store.create()
    assert "expire" not in store._nonces  # noqa: SLF001
    await store.close()
    assert store._nonces == {}  # noqa: SLF001


async def should_purge_expired_nonce_on_consume() -> None:
    store = MemoryOidcNonceStore()
    store._nonces["perime"] = 0  # noqa: SLF001 - horloge déterministe du test
    assert await store.consume("perime") is False
    assert "perime" not in store._nonces  # noqa: SLF001


async def should_cover_redis_nonce_lifecycle() -> None:
    client = AsyncMock()
    client.set = AsyncMock(side_effect=[False, True])
    client.getdel = AsyncMock(side_effect=["active", None])
    client.aclose = AsyncMock()
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.oidc_nonces.get_settings", return_value=settings),
        patch("gsie_api.auth.oidc_nonces.redis.from_url", return_value=client),
        patch("gsie_api.auth.oidc_nonces.secrets.token_urlsafe", side_effect=["a", "b"]),
    ):
        store = RedisOidcNonceStore("redis://nonce", ttl_seconds=42)
        assert store.ttl_seconds == 42
        assert await store.create() == "b"
        assert await store.consume("b") is True
        assert await store.consume("absent") is False
        await store.close()
    client.aclose.assert_awaited_once()


async def should_refuse_redis_nonce_after_five_collisions() -> None:
    client = AsyncMock()
    client.set = AsyncMock(return_value=False)
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.oidc_nonces.get_settings", return_value=settings),
        patch("gsie_api.auth.oidc_nonces.redis.from_url", return_value=client),
    ):
        store = RedisOidcNonceStore("redis://nonce")
        with pytest.raises(RuntimeError, match="nonce OIDC unique"):
            await store.create()


async def should_build_and_close_configured_nonce_stores() -> None:
    get_oidc_nonce_store.cache_clear()
    memory_settings = SimpleNamespace(
        oidc_nonce_storage_url="memory://",
        refresh_token_storage_url="redis://refresh",
        oidc_nonce_expire_seconds=12,
    )
    with patch("gsie_api.auth.oidc_nonces.get_settings", return_value=memory_settings):
        store = get_oidc_nonce_store()
        assert isinstance(store, MemoryOidcNonceStore)
        await oidc_nonces.close_oidc_nonce_store()

    redis_settings = SimpleNamespace(
        oidc_nonce_storage_url=None,
        refresh_token_storage_url="redis://refresh",
        oidc_nonce_expire_seconds=15,
    )
    redis_store = AsyncMock()
    with (
        patch("gsie_api.auth.oidc_nonces.get_settings", return_value=redis_settings),
        patch(
            "gsie_api.auth.oidc_nonces.RedisOidcNonceStore",
            return_value=redis_store,
        ),
    ):
        assert get_oidc_nonce_store() is redis_store
        await oidc_nonces.close_oidc_nonce_store()
    redis_store.close.assert_awaited_once()
