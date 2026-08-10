"""Tests du stockage objet — local, S3 fake et validation de configuration."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from gsie_api.core.config import Settings
from gsie_api.infrastructure import object_storage
from gsie_api.infrastructure.object_storage import (
    LocalStorage,
    ObjectNotFoundError,
    ObjectStorageError,
    S3Storage,
)


@pytest.fixture(autouse=True)
def reset_object_storage_singleton() -> None:
    """Isole les réglages de factory entre les tests."""
    object_storage._object_storage_instance = None
    yield
    object_storage._object_storage_instance = None


class FakeClientError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


class FakeBody:
    def __init__(self, content: bytes) -> None:
        self._content = content
        self.closed = False

    async def read(self, chunk_size: int) -> bytes:
        content, self._content = self._content[:chunk_size], self._content[chunk_size:]
        return content

    async def close(self) -> None:
        self.closed = True


class FakeS3Client:
    def __init__(self, content: bytes = b"streamed-content") -> None:
        self.content = content
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.parts: list[bytes] = []
        self.fail_upload = False

    async def put_object(self, **kwargs: Any) -> None:
        self.calls.append(("put_object", kwargs))

    async def create_multipart_upload(self, **kwargs: Any) -> dict[str, str]:
        self.calls.append(("create_multipart_upload", kwargs))
        return {"UploadId": "upload-1"}

    async def upload_part(self, **kwargs: Any) -> dict[str, str]:
        self.calls.append(("upload_part", kwargs))
        if self.fail_upload:
            raise RuntimeError("simulated upload failure")
        self.parts.append(kwargs["Body"])
        return {"ETag": f"etag-{kwargs['PartNumber']}"}

    async def complete_multipart_upload(self, **kwargs: Any) -> None:
        self.calls.append(("complete_multipart_upload", kwargs))

    async def abort_multipart_upload(self, **kwargs: Any) -> None:
        self.calls.append(("abort_multipart_upload", kwargs))

    async def get_object(self, **kwargs: Any) -> dict[str, FakeBody]:
        self.calls.append(("get_object", kwargs))
        return {"Body": FakeBody(self.content)}

    async def head_object(self, **kwargs: Any) -> dict[str, object]:
        self.calls.append(("head_object", kwargs))
        return {"ContentLength": len(self.content), "Metadata": {"sha256": "digest"}}

    async def delete_object(self, **kwargs: Any) -> None:
        self.calls.append(("delete_object", kwargs))

    def generate_presigned_url(self, operation: str, **kwargs: Any) -> str:
        self.calls.append(("generate_presigned_url", {"operation": operation, **kwargs}))
        return "http://minio.test/presigned"


class FakeClientContext:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> FakeS3Client:
        self.session.enter_count += 1
        return self.session.client

    async def __aexit__(self, *_args: object) -> None:
        self.session.exit_count += 1
        return None


class FakeSession:
    def __init__(self, client: FakeS3Client) -> None:
        self.client = client
        self.create_count = 0
        self.enter_count = 0
        self.exit_count = 0

    def create_client(self, *_args: object, **_kwargs: object) -> FakeClientContext:
        self.create_count += 1
        return FakeClientContext(self)


def _s3(client: FakeS3Client) -> S3Storage:
    return S3Storage(
        endpoint="http://minio:9000",
        access_key="access",
        secret_key="secret",
        bucket="assets",
        server_side_encryption="AES256",
        multipart_chunk_size=5 * 1024 * 1024,
        session=FakeSession(client),
    )


@pytest.mark.asyncio
async def should_reject_path_traversal_on_s3() -> None:
    storage = _s3(FakeS3Client())
    with pytest.raises(ValueError, match="outside"):
        await storage.put("../outside.txt", BytesIO(b"secret"))


@pytest.mark.asyncio
async def should_stream_multipart_and_attach_sha256_metadata() -> None:
    client = FakeS3Client()
    storage = _s3(client)
    content = b"a" * (5 * 1024 * 1024) + b"tail"

    uri = await storage.put("nested/data.bin", BytesIO(content), "application/octet-stream")

    assert uri == "s3://assets/nested/data.bin"
    assert client.parts == [content[: 5 * 1024 * 1024], b"tail"]
    create_call = next(kwargs for name, kwargs in client.calls if name == "create_multipart_upload")
    assert create_call["Metadata"] == {"sha256": hashlib.sha256(content).hexdigest()}
    assert create_call["ServerSideEncryption"] == "AES256"
    assert any(name == "complete_multipart_upload" for name, _ in client.calls)


@pytest.mark.asyncio
async def should_abort_multipart_when_upload_fails() -> None:
    client = FakeS3Client()
    client.fail_upload = True
    storage = _s3(client)

    with pytest.raises(ObjectStorageError, match="operation failed"):
        await storage.put("data.bin", BytesIO(b"a" * (5 * 1024 * 1024)))

    assert any(name == "abort_multipart_upload" for name, _ in client.calls)
    assert not any(name == "complete_multipart_upload" for name, _ in client.calls)


@pytest.mark.asyncio
async def should_get_stream_head_range_and_presigned_url_without_network() -> None:
    client = FakeS3Client(b"abcdef")
    storage = _s3(client)

    chunks = [chunk async for chunk in storage.get_stream("data.bin", start=1, end=3)]
    metadata = await storage.head("data.bin")
    result = await storage.get_range("data.bin", 1, 3)
    url = await storage.get_presigned_url("data.bin", expires_in=60)

    assert b"".join(chunks) == b"abcdef"
    assert metadata["ContentLength"] == 6
    assert result.read() == b"abcdef"
    assert url.startswith("http://minio.test")
    range_call = [kwargs for name, kwargs in client.calls if name == "get_object"][0]
    assert range_call["Range"] == "bytes=1-3"


@pytest.mark.asyncio
async def should_reuse_s3_client_pool_and_close_it_once() -> None:
    client = FakeS3Client()
    session = FakeSession(client)
    storage = S3Storage(
        endpoint="http://minio:9000",
        access_key="access",
        secret_key="secret",
        bucket="assets",
        multipart_chunk_size=5 * 1024 * 1024,
        session=session,
    )

    await storage.head("data.bin")
    await storage.delete("data.bin")
    await storage.get_presigned_url("data.bin")

    assert session.create_count == 1
    assert session.enter_count == 1
    await storage.close()
    await storage.close()
    assert session.exit_count == 1


@pytest.mark.asyncio
async def should_return_false_without_error_log_when_s3_head_reports_missing_object(
    monkeypatch,
) -> None:
    class MissingClient(FakeS3Client):
        async def head_object(self, **kwargs: Any) -> dict[str, object]:
            raise FakeClientError("NoSuchKey")

    class RecordingLogger:
        def __init__(self) -> None:
            self.debug_events: list[tuple[str, dict[str, object]]] = []
            self.error_events: list[tuple[str, dict[str, object]]] = []

        def debug(self, event: str, **kwargs: object) -> None:
            self.debug_events.append((event, kwargs))

        def error(self, event: str, **kwargs: object) -> None:
            self.error_events.append((event, kwargs))

    logger = RecordingLogger()
    monkeypatch.setattr(object_storage, "logger", logger)
    storage = _s3(MissingClient())

    assert await storage.exists("missing.bin") is False
    assert logger.error_events == []
    assert logger.debug_events[0][0] == "object_storage_object_not_found"
    assert logger.debug_events[0][1]["error_code"] == "NoSuchKey"


@pytest.mark.asyncio
async def should_preserve_local_storage_protection_and_copy_in_chunks(tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))

    await storage.put("nested/file.txt", BytesIO(b"content"))
    result = await storage.get("nested/file.txt")

    assert result.read() == b"content"
    with pytest.raises(ValueError, match="outside"):
        await storage.delete("../outside.txt")


def should_reject_invalid_s3_configuration() -> None:
    with pytest.raises(ValueError, match="credentials"):
        S3Storage("http://minio:9000", "", "secret", "assets")


def _valid_production_settings() -> dict[str, object]:
    return {
        "environment": "production",
        "database_url": "postgresql+asyncpg://gsie_app:secure@host:5432/gsie",
        "cors_origins": ["https://example.com"],
        "ws_allowed_origins": ["https://hub.example.com"],
        "redis_url": "redis://:secret@redis-host:6379/0",
        "rate_limit_storage_url": "redis://:secret@redis-host:6379/1",
        "refresh_token_storage_url": "redis://:secret@redis-host:6379/2",
        "auth_dev_login_enabled": False,
        "require_rust_backend": True,
        "db_ssl_mode": "require",
        "mfa_encryption_key": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
        "transactional_email_mode": "smtp",
        "smtp_host": "smtp.example.com",
        "smtp_starttls": True,
    }


def should_require_s3_in_production() -> None:
    with pytest.raises(ValidationError, match="S3 object storage"):
        Settings(**_valid_production_settings(), _env_file=None)


def should_reject_http_s3_endpoint_in_production() -> None:
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            **_valid_production_settings(),
            object_storage_backend="s3",
            object_storage_s3_endpoint="http://s3.example.com",
            object_storage_s3_access_key=SecretStr("access"),
            object_storage_s3_secret_key=SecretStr("secret"),
            _env_file=None,
        )


def should_require_s3_encryption_in_production() -> None:
    with pytest.raises(ValidationError, match="Chiffrement serveur S3"):
        Settings(
            **_valid_production_settings(),
            object_storage_backend="s3",
            object_storage_s3_endpoint="https://s3.example.com",
            object_storage_s3_access_key=SecretStr("access"),
            object_storage_s3_secret_key=SecretStr("secret"),
            _env_file=None,
        )


def should_accept_configured_s3_encryption_in_production() -> None:
    settings = Settings(
        **_valid_production_settings(),
        object_storage_backend="s3",
        object_storage_s3_endpoint="https://s3.example.com",
        object_storage_s3_access_key=SecretStr("access"),
        object_storage_s3_secret_key=SecretStr("secret"),
        object_storage_s3_server_side_encryption="AES256",
        _env_file=None,
    )

    assert settings.object_storage_s3_server_side_encryption == "AES256"


def should_accept_minio_http_endpoint_in_development() -> None:
    settings = Settings(
        environment="development",
        object_storage_backend="s3",
        object_storage_s3_endpoint="http://minio:9000",
        object_storage_s3_access_key=SecretStr("access"),
        object_storage_s3_secret_key=SecretStr("secret"),
        _env_file=None,
    )
    assert settings.object_storage_backend == "s3"


def should_build_s3_storage_from_factory(monkeypatch) -> None:
    monkeypatch.setattr(object_storage._settings, "environment", "development")
    monkeypatch.setattr(object_storage._settings, "object_storage_backend", "s3")
    monkeypatch.setattr(object_storage._settings, "object_storage_s3_endpoint", "http://minio:9000")
    monkeypatch.setattr(
        object_storage._settings, "object_storage_s3_access_key", SecretStr("access")
    )
    monkeypatch.setattr(
        object_storage._settings, "object_storage_s3_secret_key", SecretStr("secret")
    )

    storage = object_storage.get_object_storage()

    assert isinstance(storage, S3Storage)


def should_keep_local_storage_factory_in_development(monkeypatch) -> None:
    monkeypatch.setattr(object_storage._settings, "environment", "development")
    monkeypatch.setattr(object_storage._settings, "object_storage_backend", "local")
    assert isinstance(object_storage.get_object_storage(), LocalStorage)


def should_refuse_local_factory_in_production(monkeypatch) -> None:
    monkeypatch.setattr(object_storage._settings, "environment", "production")
    monkeypatch.setattr(object_storage._settings, "object_storage_backend", "local")
    with pytest.raises(RuntimeError, match="S3"):
        object_storage.get_object_storage()


@pytest.mark.asyncio
async def should_map_missing_s3_object_to_business_exception() -> None:
    class MissingClient(FakeS3Client):
        async def get_object(self, **kwargs: Any) -> dict[str, FakeBody]:
            raise FakeClientError("NoSuchKey")

    storage = _s3(MissingClient())
    with pytest.raises(ObjectNotFoundError, match="Object not found"):
        await storage.get("missing.bin")


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["", "bad\x00key", ".", "/absolute", "a//b", "a/./b", "a/../b"])
async def should_reject_invalid_s3_keys(key: str) -> None:
    with pytest.raises(ValueError):
        await _s3(FakeS3Client()).put(key, BytesIO(b"data"))


@pytest.mark.asyncio
async def should_reject_invalid_local_key_and_range(tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))
    await storage.put("data.txt", BytesIO(b"0123456789"))

    with pytest.raises(ValueError, match="Invalid object key"):
        await storage.get("bad\x00key")
    with pytest.raises(ValueError, match="non-negative"):
        await storage.get("data.txt", start=-1)
    with pytest.raises(ValueError, match="greater than"):
        await storage.get_stream("data.txt", start=5, end=4).__anext__()


@pytest.mark.asyncio
async def should_cover_local_stream_ranges_and_iter_chunks(tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))
    await storage.put("data.txt", BytesIO(b"0123456789"))

    ranged = [chunk async for chunk in storage.get_stream("data.txt", 2, 5, chunk_size=2)]
    ending_stream = [chunk async for chunk in storage.get_stream("data.txt", end=2, chunk_size=2)]
    iterated = [chunk async for chunk in storage.iter_chunks("data.txt", chunk_size=3)]
    ending_range = await storage.get("data.txt", end=2)
    direct_range = await storage.get_range("data.txt", 3, 5)

    assert b"".join(ranged) == b"2345"
    assert b"".join(ending_stream) == b"012"
    assert b"".join(iterated) == b"0123456789"
    assert ending_range.read() == b"012"
    assert direct_range.read() == b"345"


@pytest.mark.asyncio
async def should_cover_local_metadata_deletion_existence_and_refuse_presigned_url(tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))
    await storage.put("data.txt", BytesIO(b"data"))

    metadata = await storage.head("data.txt")
    assert metadata["content_length"] == 4
    assert await storage.exists("data.txt") is True
    assert await storage.delete("data.txt") is True
    assert await storage.delete("data.txt") is False
    assert await storage.exists("data.txt") is False
    with pytest.raises(ObjectStorageError, match="indisponible"):
        await storage.get_presigned_url("other.txt")

    with pytest.raises(ValueError, match="expiration"):
        await storage.get_presigned_url("other.txt", expires_in=0)


@pytest.mark.asyncio
async def should_cover_local_empty_stream_and_invalid_read_chunk(tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))
    await storage.put("empty.txt", BytesIO(b""))

    assert [chunk async for chunk in storage.get_stream("empty.txt")] == []
    with pytest.raises(ValueError, match="positive"):
        storage.iter_chunks("empty.txt", chunk_size=0)


def should_reject_local_path_that_is_not_relative(monkeypatch, tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))

    def always_outside(_path: Path, _base: Path) -> bool:
        return False

    monkeypatch.setattr(Path, "is_relative_to", always_outside)
    with pytest.raises(ValueError, match="outside"):
        storage._resolve_key("safe.txt")


@pytest.mark.asyncio
async def should_upload_empty_s3_object_with_sha256_metadata() -> None:
    client = FakeS3Client()
    await _s3(client).put("empty.bin", BytesIO(b""), "application/octet-stream")

    call = next(kwargs for name, kwargs in client.calls if name == "put_object")
    assert call["Body"] == b""
    assert call["Metadata"] == {"sha256": hashlib.sha256(b"").hexdigest()}
    assert call["ServerSideEncryption"] == "AES256"


@pytest.mark.asyncio
async def should_refuse_presigned_url_longer_than_fifteen_minutes() -> None:
    storage = _s3(FakeS3Client())

    with pytest.raises(ValueError, match="15 minutes"):
        await storage.get_presigned_url("data.bin", expires_in=901)


@pytest.mark.asyncio
async def should_ignore_abort_failure_and_preserve_upload_error() -> None:
    class AbortFailingClient(FakeS3Client):
        async def abort_multipart_upload(self, **kwargs: Any) -> None:
            raise RuntimeError("abort failure")

    client = AbortFailingClient()
    client.fail_upload = True
    with pytest.raises(ObjectStorageError, match="operation failed"):
        await _s3(client).put("data.bin", BytesIO(b"a" * (5 * 1024 * 1024)))


@pytest.mark.asyncio
async def should_support_s3_range_without_end_and_sync_body_close() -> None:
    class SyncCloseBody(FakeBody):
        def close(self) -> None:
            self.closed = True

    class SyncBodyClient(FakeS3Client):
        async def get_object(self, **kwargs: Any) -> dict[str, SyncCloseBody]:
            self.calls.append(("get_object", kwargs))
            return {"Body": SyncCloseBody(self.content)}

    client = SyncBodyClient(b"abcdef")
    storage = _s3(client)
    chunks = [chunk async for chunk in storage.get_stream("data.bin", start=2)]
    ending_chunks = [chunk async for chunk in storage.get_stream("data.bin", end=2)]
    ending_file = await storage.get("data.bin", end=2)

    assert b"".join(chunks) == b"abcdef"
    assert b"".join(ending_chunks) == b"abcdef"
    assert ending_file.read() == b"abcdef"
    request = next(kwargs for name, kwargs in client.calls if name == "get_object")
    assert request["Range"] == "bytes=2-"


@pytest.mark.asyncio
async def should_cover_s3_iter_chunks_and_read_range_validation() -> None:
    client = FakeS3Client(b"abc")
    storage = _s3(client)
    chunks = [chunk async for chunk in storage.iter_chunks("data.bin", chunk_size=2)]

    assert b"".join(chunks) == b"abc"
    with pytest.raises(ValueError, match="positive"):
        storage.iter_chunks("data.bin", chunk_size=0)
    with pytest.raises(ValueError, match="non-negative"):
        await storage.get("data.bin", start=-1)
    with pytest.raises(ValueError, match="greater than"):
        await storage.get_range("data.bin", 5, 4)


@pytest.mark.asyncio
async def should_translate_non_404_and_preserve_storage_errors() -> None:
    class StatusError(FakeClientError):
        def __init__(self) -> None:
            Exception.__init__(self, "service unavailable")
            self.response = {"ResponseMetadata": {"HTTPStatusCode": 503}}

    class StatusClient(FakeS3Client):
        async def head_object(self, **kwargs: Any) -> dict[str, object]:
            raise StatusError()

    with pytest.raises(ObjectStorageError, match="operation failed"):
        await _s3(StatusClient()).head("data.bin")

    storage_error = ObjectStorageError("safe")

    class PassthroughClient(FakeS3Client):
        async def head_object(self, **kwargs: Any) -> dict[str, object]:
            raise storage_error

    with pytest.raises(ObjectStorageError, match="safe") as caught:
        await _s3(PassthroughClient()).head("data.bin")
    assert caught.value is storage_error


@pytest.mark.asyncio
async def should_cover_s3_head_delete_exists_and_presigned_error_paths() -> None:
    class ErrorClient(FakeS3Client):
        async def delete_object(self, **kwargs: Any) -> None:
            raise FakeClientError("AccessDenied")

        def generate_presigned_url(self, operation: str, **kwargs: Any) -> str:
            raise FakeClientError("AccessDenied")

    storage = _s3(FakeS3Client())
    assert await storage.exists("data.bin") is True
    assert await storage.delete("data.bin") is True

    with pytest.raises(ObjectStorageError, match="delete"):
        await _s3(ErrorClient()).delete("data.bin")
    with pytest.raises(ObjectStorageError, match="presigned_url"):
        await _s3(ErrorClient()).get_presigned_url("data.bin")


@pytest.mark.asyncio
async def should_support_async_presigned_result_and_validate_expiration() -> None:
    class AsyncUrlClient(FakeS3Client):
        async def generate_url(self) -> str:
            return "https://signed.example/object"

        def generate_presigned_url(self, operation: str, **kwargs: Any) -> Any:
            return self.generate_url()

    storage = _s3(AsyncUrlClient())
    assert await storage.get_presigned_url("data.bin") == "https://signed.example/object"
    with pytest.raises(ValueError, match="expiration"):
        await storage.get_presigned_url("data.bin", expires_in=7 * 24 * 60 * 60 + 1)


def should_reject_invalid_multipart_chunk_size() -> None:
    with pytest.raises(ValueError, match="5 MiB"):
        S3Storage("http://minio:9000", "access", "secret", "assets", multipart_chunk_size=1)


@pytest.mark.asyncio
async def should_cover_close_body_without_close_method() -> None:
    class NoCloseBody:
        pass

    await object_storage._close_body(NoCloseBody())


@pytest.mark.asyncio
async def should_close_local_temporary_file_when_source_read_fails(monkeypatch, tmp_path) -> None:
    storage = LocalStorage(str(tmp_path / "objects"))
    await storage.put("data.bin", BytesIO(b"content"))
    temporary_files: list[BytesIO] = []

    def tracked_temporary_file(**_kwargs: Any) -> BytesIO:
        result = BytesIO()
        temporary_files.append(result)
        return result

    def failing_open(_path: Path, *_args: object, **_kwargs: object) -> BytesIO:
        raise OSError("lecture locale simulée en échec")

    monkeypatch.setattr(object_storage.tempfile, "SpooledTemporaryFile", tracked_temporary_file)
    monkeypatch.setattr(Path, "open", failing_open)

    with pytest.raises(OSError, match="lecture locale"):
        await storage.get("data.bin")
    assert len(temporary_files) == 1
    assert temporary_files[0].closed is True


@pytest.mark.asyncio
async def should_close_s3_temporary_file_when_stream_fails(monkeypatch) -> None:
    class FailingClient(FakeS3Client):
        async def get_object(self, **kwargs: Any) -> dict[str, FakeBody]:
            raise FakeClientError("AccessDenied")

    temporary_files: list[BytesIO] = []

    def tracked_temporary_file(**_kwargs: Any) -> BytesIO:
        result = BytesIO()
        temporary_files.append(result)
        return result

    monkeypatch.setattr(object_storage.tempfile, "SpooledTemporaryFile", tracked_temporary_file)

    with pytest.raises(ObjectStorageError, match="operation failed"):
        await _s3(FailingClient()).get("data.bin")
    assert len(temporary_files) == 1
    assert temporary_files[0].closed is True
