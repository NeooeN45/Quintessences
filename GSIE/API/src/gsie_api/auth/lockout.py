"""Lockout progressif — blocage temporaire après tentatives échouées.

Utilise Redis pour un compteur distribué atomique. En développement,
un registre mémoire local suffit. Le seuil et la durée sont configurables.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from time import time
from typing import Protocol

import redis.asyncio as redis

from gsie_api.core.config import get_settings


class LockoutStore(Protocol):
    """Contrat du registre de lockout."""

    async def record_failure(self, key: str) -> int:
        """Incrémente le compteur d'échecs et retourne le nouveau total."""

    async def record_success(self, key: str) -> None:
        """Réinitialise le compteur après une authentification réussie."""

    async def is_locked(self, key: str) -> bool:
        """Indique si la clé est actuellement verrouillée."""

    async def remaining_lock_seconds(self, key: str) -> int:
        """Durée restante de verrouillage en secondes (0 si déverrouillé)."""

    async def close(self) -> None: ...


class MemoryLockoutStore:
    """Registre local réservé au développement et aux tests."""

    def __init__(self, max_attempts: int, lock_duration_seconds: int) -> None:
        self._max_attempts = max_attempts
        self._lock_duration = lock_duration_seconds
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def record_failure(self, key: str) -> int:
        async with self._lock:
            now = time()
            self._failures.setdefault(key, []).append(now)
            self._failures[key] = [t for t in self._failures[key] if now - t < self._lock_duration]
            count = len(self._failures[key])
            if count >= self._max_attempts:
                self._locked_until[key] = now + self._lock_duration
            return count

    async def record_success(self, key: str) -> None:
        async with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)

    async def is_locked(self, key: str) -> bool:
        async with self._lock:
            until = self._locked_until.get(key)
            if until is None:
                return False
            if time() >= until:
                del self._locked_until[key]
                self._failures.pop(key, None)
                return False
            return True

    async def remaining_lock_seconds(self, key: str) -> int:
        async with self._lock:
            until = self._locked_until.get(key)
            if until is None:
                return 0
            remaining = until - time()
            return max(0, int(remaining))

    async def close(self) -> None:
        self._failures.clear()
        self._locked_until.clear()


class RedisLockoutStore:
    """Registre distribué Redis avec fenêtre glissante atomique."""

    _KEY_PREFIX = "gsie:auth:lockout:"
    _FAIL_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local max_attempts = tonumber(ARGV[3])
    local lock_duration = tonumber(ARGV[4])

    redis.call("ZREMRANGEBYSCORE", key, 0, now - window)
    local count = redis.call("ZCARD", key)
    count = count + 1
    redis.call("ZADD", key, now, now .. ":" .. count)
    redis.call("EXPIRE", key, math.ceil(window))

    if count >= max_attempts then
        local lock_key = key .. ":locked"
        redis.call("SET", lock_key, "1", "EX", lock_duration)
        return count
    end
    return count
    """

    def __init__(self, url: str, max_attempts: int, lock_duration_seconds: int) -> None:
        settings = get_settings()
        self._max_attempts = max_attempts
        self._lock_duration = lock_duration_seconds
        self._client = redis.from_url(  # type: ignore[no-untyped-call]
            url,
            decode_responses=True,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_connect_timeout,
        )

    async def record_failure(self, key: str) -> int:
        result = await self._client.eval(
            self._FAIL_SCRIPT,
            1,
            f"{self._KEY_PREFIX}{key}",
            str(time()),
            str(self._lock_duration * 2),
            str(self._max_attempts),
            str(self._lock_duration),
        )
        return int(result)

    async def record_success(self, key: str) -> None:
        prefixed = f"{self._KEY_PREFIX}{key}"
        await self._client.delete(prefixed, f"{prefixed}:locked")

    async def is_locked(self, key: str) -> bool:
        value = await self._client.get(f"{self._KEY_PREFIX}{key}:locked")
        return value is not None

    async def remaining_lock_seconds(self, key: str) -> int:
        ttl = await self._client.ttl(f"{self._KEY_PREFIX}{key}:locked")
        return max(0, int(ttl))

    async def close(self) -> None:
        await self._client.aclose()


@lru_cache
def get_lockout_store() -> LockoutStore:
    """Construit le registre configuré pour le processus."""
    settings = get_settings()
    max_attempts = settings.lockout_max_attempts
    lock_duration = settings.lockout_duration_minutes * 60
    storage_url = settings.refresh_token_storage_url
    if storage_url == "memory://":
        return MemoryLockoutStore(max_attempts, lock_duration)
    return RedisLockoutStore(storage_url, max_attempts, lock_duration)


async def close_lockout_store() -> None:
    store = get_lockout_store()
    await store.close()
    get_lockout_store.cache_clear()


class AccountLockoutService:
    """Service de lockout — clé composite email + IP."""

    def __init__(self, store: LockoutStore) -> None:
        self._store = store
        self._settings = get_settings()

    def _key(self, email: str, ip_address: str | None) -> str:
        return f"{email}:{ip_address or 'unknown'}"

    async def check_and_raise(self, email: str, ip_address: str | None) -> None:
        """Lève une exception si le compte est verrouillé."""
        key = self._key(email, ip_address)
        if await self._store.is_locked(key):
            remaining = await self._store.remaining_lock_seconds(key)
            raise AccountLockedError(remaining_seconds=remaining)

    async def record_failure(self, email: str, ip_address: str | None) -> None:
        key = self._key(email, ip_address)
        await self._store.record_failure(key)

    async def record_success(self, email: str, ip_address: str | None) -> None:
        key = self._key(email, ip_address)
        await self._store.record_success(key)


class AccountLockedError(Exception):
    """Le compte est temporairement verrouillé après trop de tentatives."""

    def __init__(self, remaining_seconds: int) -> None:
        self.remaining_seconds = remaining_seconds
        super().__init__(f"Compte verrouillé pour {remaining_seconds}s")
