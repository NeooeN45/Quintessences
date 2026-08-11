"""Worker FETCH borné, fail-closed et sans création implicite de DataAsset."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from gsie_api.data.adapters import (
    AdapterCapability,
    AdapterCapabilityError,
    AdapterSecurityError,
)

if TYPE_CHECKING:
    from gsie_api.data.adapters import AdapterContext, AdapterFetchRequest, DataSourceAdapter
    from gsie_api.data.fetch_policy import FetchQualificationRegistry


class FetchSink(Protocol):
    """Destination transactionnelle : commit uniquement après toutes les preuves."""

    async def write(self, chunk: bytes) -> None: ...

    async def commit(self) -> None: ...

    async def abort(self) -> None: ...


@dataclass(frozen=True, slots=True)
class BoundedFetchReceipt:
    """Preuve du flux reçu ; ce reçu n'est pas encore un DataAsset RAW."""

    size_bytes: int
    checksum_sha256: str
    content_type: str


def _base_content_type(value: str | None) -> str:
    return (value or "").partition(";")[0].strip().lower()


class BoundedFetchWorker:
    """Qualifie puis reçoit un flux sans jamais dépasser les bornes autorisées."""

    def __init__(
        self,
        qualifications: FetchQualificationRegistry,
        *,
        abort_timeout_seconds: float = 5.0,
    ) -> None:
        if not 0 < abort_timeout_seconds <= 30:
            raise ValueError("abort_timeout_seconds doit être compris entre 0 et 30")
        self._qualifications = qualifications
        self._abort_timeout_seconds = abort_timeout_seconds

    async def _abort(self, sink: FetchSink) -> None:
        try:
            async with asyncio.timeout(self._abort_timeout_seconds):
                await sink.abort()
        except TimeoutError as exc:
            raise AdapterSecurityError("FETCH_ABORT_TIMEOUT") from exc

    async def fetch(
        self,
        *,
        source_registry_id: str,
        adapter: DataSourceAdapter,
        request: AdapterFetchRequest,
        context: AdapterContext,
        sink: FetchSink,
    ) -> BoundedFetchReceipt:
        decision = self._qualifications.require_fetch_allowed(source_registry_id)
        if not adapter.supports(AdapterCapability.FETCH):
            raise AdapterCapabilityError("l'adapter ne déclare pas la capacité fetch")
        adapter.validate_target_url(request.distribution_url)
        limit = min(request.max_bytes, context.max_bytes, decision.max_bytes or 0)
        if request.max_bytes > (decision.max_bytes or 0):
            raise AdapterSecurityError("FETCH_SIZE_LIMIT_EXCEEDED: limite de qualification")
        if request.max_bytes > context.max_bytes:
            raise AdapterSecurityError("FETCH_SIZE_LIMIT_EXCEEDED: limite du contexte")

        try:
            async with asyncio.timeout(context.timeout_seconds):
                result = await adapter.fetch(request, context)
                content_type = _base_content_type(result.content_type)
                allowed_types = {item.lower() for item in decision.allowed_content_types}
                if content_type not in allowed_types:
                    raise AdapterSecurityError("FETCH_CONTENT_TYPE_REJECTED")
                if result.content_length is not None and result.content_length > limit:
                    raise AdapterSecurityError("FETCH_SIZE_LIMIT_EXCEEDED: Content-Length")

                digest = hashlib.sha256()
                size = 0
                async for chunk in result.body:
                    if not isinstance(chunk, bytes) or not chunk:
                        raise AdapterSecurityError("FETCH_CHUNK_INVALID")
                    size += len(chunk)
                    if size > limit:
                        raise AdapterSecurityError("FETCH_SIZE_LIMIT_EXCEEDED: flux réel")
                    digest.update(chunk)
                    await sink.write(chunk)
                if size == 0:
                    raise AdapterSecurityError("FETCH_EMPTY_BODY")
                checksum = digest.hexdigest()
                if request.expected_checksum is not None and (
                    checksum != request.expected_checksum.lower()
                ):
                    raise AdapterSecurityError("FETCH_CHECKSUM_MISMATCH")
                await sink.commit()
                return BoundedFetchReceipt(
                    size_bytes=size,
                    checksum_sha256=checksum,
                    content_type=content_type,
                )
        except TimeoutError as exc:
            await self._abort(sink)
            raise AdapterSecurityError("FETCH_TIMEOUT") from exc
        except BaseException:
            await self._abort(sink)
            raise


__all__ = ["BoundedFetchReceipt", "BoundedFetchWorker", "FetchSink"]
