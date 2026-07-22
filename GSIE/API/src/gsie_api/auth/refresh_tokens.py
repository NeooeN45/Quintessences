"""Registre de rotation des refresh tokens.

Chaque identifiant JWT est enregistre lors de l'emission puis consomme
atomiquement au premier rafraichissement. Redis est obligatoire hors
developpement afin que cette garantie reste vraie avec plusieurs workers.
"""

import asyncio
import math
from functools import lru_cache
from time import time
from typing import Protocol

import redis.asyncio as redis

from gsie_api.core.config import get_settings


class RefreshTokenStore(Protocol):
    """Contrat minimal d'un registre de refresh tokens."""

    async def register(self, jti: str, expires_at: float) -> None:
        """Enregistre un token nouvellement emis."""

    async def consume(self, jti: str) -> bool:
        """Consomme un token et retourne False s'il est absent ou expire."""

    async def rotate(self, current_jti: str, new_jti: str, expires_at: float) -> bool:
        """Remplace atomiquement un token actif par son successeur."""

    async def close(self) -> None:
        """Ferme les ressources du registre."""


class MemoryRefreshTokenStore:
    """Registre local reserve au developpement et aux tests."""

    def __init__(self) -> None:
        self._tokens: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def register(self, jti: str, expires_at: float) -> None:
        async with self._lock:
            self._purge_expired()
            self._tokens[jti] = expires_at

    async def consume(self, jti: str) -> bool:
        async with self._lock:
            self._purge_expired()
            expires_at = self._tokens.pop(jti, None)
            return expires_at is not None and expires_at > time()

    async def rotate(self, current_jti: str, new_jti: str, expires_at: float) -> bool:
        async with self._lock:
            self._purge_expired()
            current_expires_at = self._tokens.get(current_jti)
            if current_expires_at is None or current_expires_at <= time():
                return False
            if new_jti in self._tokens:
                raise RuntimeError("Refresh token identifier collision")
            del self._tokens[current_jti]
            self._tokens[new_jti] = expires_at
            return True

    async def close(self) -> None:
        """Aucune ressource externe à fermer pour le registre mémoire."""

    def _purge_expired(self) -> None:
        now = time()
        expired = [jti for jti, expires_at in self._tokens.items() if expires_at <= now]
        for jti in expired:
            del self._tokens[jti]


class RedisRefreshTokenStore:
    """Registre distribue reposant sur des operations Redis atomiques."""

    _KEY_PREFIX = "gsie:auth:refresh:"
    _ROTATE_SCRIPT = """
    local current = redis.call("GET", KEYS[1])
    if current ~= "active" then
        return 0
    end
    if redis.call("EXISTS", KEYS[2]) == 1 then
        return -1
    end
    redis.call("SET", KEYS[2], "active", "EX", ARGV[1])
    redis.call("DEL", KEYS[1])
    return 1
    """

    def __init__(self, url: str) -> None:
        settings = get_settings()
        self._client = redis.from_url(  # type: ignore[no-untyped-call]
            url,
            decode_responses=True,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_connect_timeout,
        )

    async def register(self, jti: str, expires_at: float) -> None:
        ttl = max(1, math.ceil(expires_at - time()))
        created = await self._client.set(
            f"{self._KEY_PREFIX}{jti}",
            "active",
            ex=ttl,
            nx=True,
        )
        if not created:
            raise RuntimeError("Refresh token identifier collision")

    async def consume(self, jti: str) -> bool:
        value = await self._client.getdel(f"{self._KEY_PREFIX}{jti}")
        return str(value) == "active"

    async def rotate(self, current_jti: str, new_jti: str, expires_at: float) -> bool:
        ttl = max(1, math.ceil(expires_at - time()))
        result = await self._client.eval(
            self._ROTATE_SCRIPT,
            2,
            f"{self._KEY_PREFIX}{current_jti}",
            f"{self._KEY_PREFIX}{new_jti}",
            ttl,
        )
        code = int(result)
        if code == -1:
            raise RuntimeError("Refresh token identifier collision")
        return code == 1

    async def close(self) -> None:
        await self._client.aclose()


@lru_cache
def get_refresh_token_store() -> RefreshTokenStore:
    """Construit le registre configure pour le processus courant."""
    settings = get_settings()
    if settings.refresh_token_storage_url == "memory://":
        return MemoryRefreshTokenStore()
    return RedisRefreshTokenStore(settings.refresh_token_storage_url)


async def close_refresh_token_store() -> None:
    """Ferme le registre courant et invalide le singleton de processus."""
    store = get_refresh_token_store()
    await store.close()
    get_refresh_token_store.cache_clear()
