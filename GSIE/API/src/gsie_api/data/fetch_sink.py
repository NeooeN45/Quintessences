"""Destination transactionnelle du worker FETCH vers ObjectStorage/MinIO."""

from __future__ import annotations

import asyncio
import re
import tempfile
from typing import TYPE_CHECKING, BinaryIO, cast

if TYPE_CHECKING:
    from gsie_api.infrastructure.object_storage import ObjectStorage

_RAW_KEY = re.compile(r"^raw/fetch/[a-z0-9][a-z0-9._/-]{0,399}$")


class TransactionalFetchSinkError(RuntimeError):
    """Échec d'état ou de publication du sink transactionnel."""


class TransactionalObjectStorageSink:
    """Spool privé puis publication S3 atomique uniquement lors du commit."""

    def __init__(
        self,
        storage: ObjectStorage,
        *,
        final_key: str,
        content_type: str,
        spool_max_bytes: int,
    ) -> None:
        if not _RAW_KEY.fullmatch(final_key) or ".." in final_key:
            raise ValueError("final_key doit rester sous raw/fetch/")
        if not content_type.strip():
            raise ValueError("content_type obligatoire")
        if spool_max_bytes <= 0:
            raise ValueError("spool_max_bytes doit être positif")
        self._storage = storage
        self._final_key = final_key
        self._content_type = content_type.strip().lower()
        self._spool: BinaryIO = cast(
            BinaryIO,
            tempfile.SpooledTemporaryFile(  # noqa: SIM115 - cycle de vie piloté par commit/abort
                max_size=spool_max_bytes, mode="w+b"
            ),
        )
        self._committed = False
        self._closed = False
        self._publication_started = False
        self._storage_uri: str | None = None

    @property
    def storage_uri(self) -> str | None:
        return self._storage_uri

    async def write(self, chunk: bytes) -> None:
        if self._closed or self._committed:
            raise TransactionalFetchSinkError("écriture interdite après finalisation")
        await asyncio.to_thread(self._spool.write, chunk)

    async def commit(self) -> None:
        if self._closed or self._committed:
            raise TransactionalFetchSinkError("sink déjà finalisé")
        if await self._storage.exists(self._final_key):
            raise TransactionalFetchSinkError("la clé RAW existe déjà")
        await asyncio.to_thread(self._spool.seek, 0)
        self._publication_started = True
        self._storage_uri = await self._storage.put(
            self._final_key,
            self._spool,
            self._content_type,
        )
        await self._close_spool()
        self._committed = True

    async def abort(self) -> None:
        if self._committed:
            return
        if self._publication_started:
            await self._storage.delete(self._final_key)
        if not self._closed:
            await self._close_spool()

    async def _close_spool(self) -> None:
        await asyncio.to_thread(self._spool.close)
        self._closed = True


__all__ = ["TransactionalFetchSinkError", "TransactionalObjectStorageSink"]
