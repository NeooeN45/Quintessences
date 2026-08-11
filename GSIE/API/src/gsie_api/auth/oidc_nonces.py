"""Registre de nonces OIDC génériques courts et à usage unique.

Miroir de ``google_nonces.py`` pour le flux OIDC enterprise (Keycloak,
Entra ID, etc.) — voir PENTEST_AUTH_CONNEXION_2026-08-07.md §2.1.
"""

from __future__ import annotations

import asyncio
import secrets
from functools import lru_cache
from time import time
from typing import Protocol

import redis.asyncio as redis

from gsie_api.core.config import get_settings


class OidcNonceStore(Protocol):
    """Contrat du registre anti-rejeu OIDC."""

    @property
    def ttl_seconds(self) -> int: ...

    async def create(self) -> str: ...

    async def consume(self, nonce: str) -> bool: ...

    async def close(self) -> None: ...


class MemoryOidcNonceStore:
    """Registre local réservé au développement et aux tests."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl_seconds = ttl_seconds
        self._nonces: dict[str, float] = {}
        self._lock = asyncio.Lock()

    @property
    def ttl_seconds(self) -> int:
        return self._ttl_seconds

    async def create(self) -> str:
        async with self._lock:
            self._purge_expired()
            while True:
                nonce = secrets.token_urlsafe(32)
                if nonce not in self._nonces:
                    self._nonces[nonce] = time() + self._ttl_seconds
                    return nonce

    async def consume(self, nonce: str) -> bool:
        async with self._lock:
            self._purge_expired()
            expires_at = self._nonces.pop(nonce, None)
            return expires_at is not None and expires_at > time()

    async def close(self) -> None:
        self._nonces.clear()

    def _purge_expired(self) -> None:
        now = time()
        for nonce in [key for key, expires_at in self._nonces.items() if expires_at <= now]:
            del self._nonces[nonce]


class RedisOidcNonceStore:
    """Registre distribué utilisant GETDEL pour une consommation atomique."""

    _KEY_PREFIX = "gsie:auth:oidc-nonce:"

    def __init__(self, url: str, ttl_seconds: int = 300) -> None:
        settings = get_settings()
        self._ttl_seconds = ttl_seconds
        self._client = redis.from_url(  # type: ignore[no-untyped-call]
            url,
            decode_responses=True,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_connect_timeout,
        )

    @property
    def ttl_seconds(self) -> int:
        return self._ttl_seconds

    async def create(self) -> str:
        for _ in range(5):
            nonce = secrets.token_urlsafe(32)
            created = await self._client.set(
                f"{self._KEY_PREFIX}{nonce}",
                "active",
                ex=self._ttl_seconds,
                nx=True,
            )
            if created:
                return nonce
        raise RuntimeError("Impossible de produire un nonce OIDC unique")

    async def consume(self, nonce: str) -> bool:
        value = await self._client.getdel(f"{self._KEY_PREFIX}{nonce}")
        return str(value) == "active"

    async def close(self) -> None:
        await self._client.aclose()


@lru_cache
def get_oidc_nonce_store() -> OidcNonceStore:
    """Construit le registre configuré pour le processus."""
    settings = get_settings()
    storage_url = settings.oidc_nonce_storage_url or settings.refresh_token_storage_url
    ttl_seconds = settings.oidc_nonce_expire_seconds
    if storage_url == "memory://":
        return MemoryOidcNonceStore(ttl_seconds)
    return RedisOidcNonceStore(storage_url, ttl_seconds)


async def close_oidc_nonce_store() -> None:
    store = get_oidc_nonce_store()
    await store.close()
    get_oidc_nonce_store.cache_clear()
