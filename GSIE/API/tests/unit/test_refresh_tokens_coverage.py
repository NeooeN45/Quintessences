"""Couverture résiduelle de auth/refresh_tokens.py — revoke() et is_revoked().

Ces deux méthodes du contrat ``RefreshTokenStore`` (utilisées par le logout
et la détection de réutilisation) n'étaient exercées ni pour le registre
mémoire ni pour le registre Redis.
"""

from __future__ import annotations

from time import time
from unittest.mock import AsyncMock

from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore, RedisRefreshTokenStore


class TestMemoryRefreshTokenStoreRevoke:
    async def should_revoke_registered_token(self) -> None:
        store = MemoryRefreshTokenStore()
        await store.register("jti-1", time() + 60)

        assert await store.revoke("jti-1") is True
        # Un jeton déjà révoqué ne peut plus l'être une deuxième fois.
        assert await store.revoke("jti-1") is False

    async def should_not_revoke_unknown_token(self) -> None:
        store = MemoryRefreshTokenStore()

        assert await store.revoke("absent") is False

    async def should_report_revoked_for_unknown_token(self) -> None:
        store = MemoryRefreshTokenStore()

        assert await store.is_revoked("absent") is True

    async def should_report_not_revoked_for_registered_token(self) -> None:
        store = MemoryRefreshTokenStore()
        await store.register("jti-1", time() + 60)

        assert await store.is_revoked("jti-1") is False

    async def should_report_revoked_once_token_is_purged_expired(self) -> None:
        store = MemoryRefreshTokenStore()
        await store.register("jti-1", time() - 1)  # déjà expiré

        assert await store.is_revoked("jti-1") is True


class TestRedisRefreshTokenStoreRevoke:
    @staticmethod
    def _store() -> RedisRefreshTokenStore:
        store = RedisRefreshTokenStore("redis://localhost:6379/0")
        store._client = AsyncMock()  # évite toute connexion Redis réelle
        return store

    async def should_revoke_existing_key(self) -> None:
        store = self._store()
        store._client.delete = AsyncMock(return_value=1)

        assert await store.revoke("jti-1") is True
        store._client.delete.assert_awaited_once_with("gsie:auth:refresh:jti-1")

    async def should_not_revoke_missing_key(self) -> None:
        store = self._store()
        store._client.delete = AsyncMock(return_value=0)

        assert await store.revoke("jti-1") is False

    async def should_report_not_revoked_when_key_present(self) -> None:
        store = self._store()
        store._client.get = AsyncMock(return_value="active")

        assert await store.is_revoked("jti-1") is False

    async def should_report_revoked_when_key_absent(self) -> None:
        store = self._store()
        store._client.get = AsyncMock(return_value=None)

        assert await store.is_revoked("jti-1") is True
