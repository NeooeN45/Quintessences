"""Couverture du registre de lockout — fermeture, backend Redis, fabrique."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from gsie_api.auth import lockout
from gsie_api.auth.lockout import (
    AccountLockoutService,
    MemoryLockoutStore,
    RedisLockoutStore,
    get_lockout_store,
)


async def should_reset_account_and_composite_counters_on_success() -> None:
    store = MemoryLockoutStore(max_attempts=2, lock_duration_seconds=60)
    service = AccountLockoutService(store)
    await service.record_failure("user@example.com", "127.0.0.1")

    await service.record_success("user@example.com", "127.0.0.1")

    await service.check_and_raise("user@example.com", "127.0.0.1")


async def should_close_memory_store_and_clear_state() -> None:
    store = MemoryLockoutStore(max_attempts=3, lock_duration_seconds=60)
    key = "user@example.com:127.0.0.1"
    await store.record_failure(key)
    await store.close()
    assert store._failures == {}  # noqa: SLF001
    assert store._locked_until == {}  # noqa: SLF001


async def should_compute_remaining_lock_seconds_for_locked_key() -> None:
    store = MemoryLockoutStore(max_attempts=1, lock_duration_seconds=60)
    key = "user@example.com:127.0.0.1"
    await store.record_failure(key)
    remaining = await store.remaining_lock_seconds(key)
    assert 0 < remaining <= 60


async def should_report_zero_remaining_seconds_when_not_locked() -> None:
    store = MemoryLockoutStore(max_attempts=3, lock_duration_seconds=60)
    assert await store.remaining_lock_seconds("absent") == 0


async def should_record_redis_failure_via_lua_script() -> None:
    client = AsyncMock()
    client.eval = AsyncMock(return_value=3)
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.lockout.get_settings", return_value=settings),
        patch("gsie_api.auth.lockout.redis.from_url", return_value=client),
    ):
        store = RedisLockoutStore("redis://lockout", max_attempts=3, lock_duration_seconds=60)
        count = await store.record_failure("user@example.com:127.0.0.1")

    assert count == 3
    client.eval.assert_awaited_once()


async def should_reset_redis_counters_on_success() -> None:
    client = AsyncMock()
    client.delete = AsyncMock()
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.lockout.get_settings", return_value=settings),
        patch("gsie_api.auth.lockout.redis.from_url", return_value=client),
    ):
        store = RedisLockoutStore("redis://lockout", max_attempts=3, lock_duration_seconds=60)
        await store.record_success("user@example.com:127.0.0.1")

    client.delete.assert_awaited_once_with(
        "gsie:auth:lockout:user@example.com:127.0.0.1",
        "gsie:auth:lockout:user@example.com:127.0.0.1:locked",
    )


async def should_report_redis_lock_state_and_remaining_seconds() -> None:
    client = AsyncMock()
    client.get = AsyncMock(side_effect=["1", None])
    client.ttl = AsyncMock(side_effect=[42, -2])
    client.aclose = AsyncMock()
    settings = SimpleNamespace(redis_socket_timeout=1.0, redis_connect_timeout=1.0)
    with (
        patch("gsie_api.auth.lockout.get_settings", return_value=settings),
        patch("gsie_api.auth.lockout.redis.from_url", return_value=client),
    ):
        store = RedisLockoutStore("redis://lockout", max_attempts=3, lock_duration_seconds=60)
        assert await store.is_locked("a") is True
        assert await store.is_locked("b") is False
        assert await store.remaining_lock_seconds("a") == 42
        assert await store.remaining_lock_seconds("b") == 0
        await store.close()

    client.aclose.assert_awaited_once()


async def should_build_and_close_configured_lockout_stores() -> None:
    get_lockout_store.cache_clear()
    memory_settings = SimpleNamespace(
        lockout_max_attempts=5,
        lockout_duration_minutes=15,
        refresh_token_storage_url="memory://",
    )
    with patch("gsie_api.auth.lockout.get_settings", return_value=memory_settings):
        store = get_lockout_store()
        assert isinstance(store, MemoryLockoutStore)
        await lockout.close_lockout_store()

    redis_settings = SimpleNamespace(
        lockout_max_attempts=5,
        lockout_duration_minutes=15,
        refresh_token_storage_url="redis://refresh",
    )
    redis_store = AsyncMock()
    with (
        patch("gsie_api.auth.lockout.get_settings", return_value=redis_settings),
        patch("gsie_api.auth.lockout.RedisLockoutStore", return_value=redis_store),
    ):
        assert get_lockout_store() is redis_store
        await lockout.close_lockout_store()
    redis_store.close.assert_awaited_once()
