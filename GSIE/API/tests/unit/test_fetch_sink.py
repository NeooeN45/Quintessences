"""Tests du sink ObjectStorage transactionnel, sans réseau."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock

import pytest

from gsie_api.data.fetch_sink import (
    TransactionalFetchSinkError,
    TransactionalObjectStorageSink,
)

if TYPE_CHECKING:
    from gsie_api.infrastructure.object_storage import ObjectStorage


def _storage(*, exists: bool = False) -> SimpleNamespace:
    captured: list[bytes] = []

    async def put(_key: str, data: object, _content_type: str) -> str:
        captured.append(data.read())  # type: ignore[attr-defined]
        return "s3://gsie-assets/raw/fetch/test.tif"

    return SimpleNamespace(
        exists=AsyncMock(return_value=exists),
        put=AsyncMock(side_effect=put),
        delete=AsyncMock(return_value=True),
        captured=captured,
    )


def _sink(storage: SimpleNamespace) -> TransactionalObjectStorageSink:
    return TransactionalObjectStorageSink(
        cast("ObjectStorage", storage),
        final_key="raw/fetch/soilgrids/test.tif",
        content_type="image/tiff",
        spool_max_bytes=1024,
    )


@pytest.mark.asyncio
async def test_abort_never_publishes_an_object() -> None:
    storage = _storage()
    sink = _sink(storage)
    await sink.write(b"partial")

    await sink.abort()

    storage.exists.assert_not_awaited()
    storage.put.assert_not_awaited()
    storage.delete.assert_not_awaited()
    assert sink.storage_uri is None


@pytest.mark.asyncio
async def test_commit_publishes_once_after_rewinding_the_spool() -> None:
    storage = _storage()
    sink = _sink(storage)
    await sink.write(b"geo")
    await sink.write(b"tiff")

    await sink.commit()

    storage.put.assert_awaited_once()
    args = storage.put.await_args.args
    assert args[0] == "raw/fetch/soilgrids/test.tif"
    assert storage.captured == [b"geotiff"]
    assert args[2] == "image/tiff"
    assert sink.storage_uri == "s3://gsie-assets/raw/fetch/test.tif"
    storage.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_raw_key_is_never_overwritten() -> None:
    storage = _storage(exists=True)
    sink = _sink(storage)
    await sink.write(b"data")

    with pytest.raises(TransactionalFetchSinkError, match="existe déjà"):
        await sink.commit()

    storage.put.assert_not_awaited()
    await sink.abort()


@pytest.mark.asyncio
async def test_abort_removes_a_possibly_published_object_after_commit_failure() -> None:
    storage = _storage()
    storage.put = AsyncMock(side_effect=RuntimeError("réponse S3 perdue"))
    sink = _sink(storage)
    await sink.write(b"data")

    with pytest.raises(RuntimeError, match="réponse S3 perdue"):
        await sink.commit()
    await sink.abort()

    storage.delete.assert_awaited_once_with("raw/fetch/soilgrids/test.tif")


@pytest.mark.asyncio
async def test_sink_rejects_writes_after_commit_or_abort() -> None:
    committed = _sink(_storage())
    await committed.write(b"data")
    await committed.commit()
    with pytest.raises(TransactionalFetchSinkError):
        await committed.write(b"late")

    aborted = _sink(_storage())
    await aborted.abort()
    with pytest.raises(TransactionalFetchSinkError):
        await aborted.write(b"late")


@pytest.mark.parametrize("key", ["staging/file.tif", "raw/fetch/../secret", "/raw/fetch/x"])
def test_sink_rejects_unsafe_or_non_raw_keys(key: str) -> None:
    with pytest.raises(ValueError, match="raw/fetch"):
        TransactionalObjectStorageSink(
            cast("ObjectStorage", _storage()),
            final_key=key,
            content_type="image/tiff",
            spool_max_bytes=1024,
        )
