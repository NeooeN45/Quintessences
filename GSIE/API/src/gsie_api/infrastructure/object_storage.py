"""Object Storage abstraction (ADR-006) — S3/MinIO/local.

Abstraction unifiée pour stocker et récupérer les DataAssets
(fichiers NetCDF, GeoTIFF, LAZ, Parquet). En dev : filesystem local.
En prod : S3-compatible (MinIO, AWS S3, Scaleway).
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import tempfile
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, cast
from urllib.parse import quote

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from aiobotocore.session import AioSession, get_session  # type: ignore[import-untyped]

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger

logger = get_logger("gsie_api.infrastructure.object_storage")
_settings = get_settings()
_DEFAULT_CHUNK_SIZE = 64 * 1024
_MIN_MULTIPART_CHUNK_SIZE = 5 * 1024 * 1024
_DEFAULT_PRESIGNED_EXPIRES = 5 * 60
_MAX_PRESIGNED_EXPIRES = 15 * 60


class ObjectStorageError(RuntimeError):
    """Erreur technique de stockage sans détail sensible."""


class ObjectNotFoundError(ObjectStorageError):
    """Objet absent du stockage."""


ObjectMetadata = dict[str, object]


def _validate_key(key: str) -> str:
    """Refuse les clés vides, absolues ou contenant une traversée de chemin."""
    if not key or "\x00" in key:
        raise ValueError("Invalid object key")
    normalized = key.replace("\\", "/")
    parts = normalized.split("/")
    if normalized.startswith("/") or any(part in ("", ".", "..") for part in parts):
        raise ValueError("Object key resolves outside configured storage")
    return normalized


def _key_fingerprint(key: str) -> str:
    """Identifiant non réversible utilisable dans les journaux."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _error_code(error: BaseException) -> str:
    response = getattr(error, "response", {})
    if isinstance(response, dict):
        error_data = response.get("Error", {})
        if isinstance(error_data, dict):
            code = error_data.get("Code")
            if code:
                return str(code)
        metadata = response.get("ResponseMetadata", {})
        if isinstance(metadata, dict) and metadata.get("HTTPStatusCode"):
            return str(metadata["HTTPStatusCode"])
    return type(error).__name__


def _translate_error(operation: str, key: str, error: Exception) -> ObjectStorageError:
    if isinstance(error, ObjectStorageError):
        return error
    code = _error_code(error)
    logger.error(
        "object_storage_operation_failed",
        operation=operation,
        key_fingerprint=_key_fingerprint(key),
        error_code=code,
    )
    if code in {"404", "NoSuchKey", "NotFound", "NoSuchObject"}:
        return ObjectNotFoundError("Object not found")
    return ObjectStorageError(f"Object storage operation failed: {operation}")


async def _close_body(body: Any) -> None:
    close = getattr(body, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


def _copy_and_hash(source: BinaryIO, target: BinaryIO, chunk_size: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    while chunk := source.read(chunk_size):
        target.write(chunk)
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


class ObjectStorage(ABC):
    """Interface abstraite pour le stockage objet."""

    @abstractmethod
    async def put(
        self, key: str, data: BinaryIO, content_type: str = "application/octet-stream"
    ) -> str:
        """Stocke un objet et retourne son URI."""

    @abstractmethod
    async def get(self, key: str, start: int | None = None, end: int | None = None) -> BinaryIO:
        """Récupère un objet dans un fichier temporaire repositionné au début."""

    @abstractmethod
    def get_stream(
        self,
        key: str,
        start: int | None = None,
        end: int | None = None,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> AsyncIterator[bytes]:
        """Diffuse un objet ou une plage sans le charger entièrement."""

    @abstractmethod
    def iter_chunks(self, key: str, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> AsyncIterator[bytes]:
        """Retourne un itérateur asynchrone de blocs."""

    @abstractmethod
    async def get_range(self, key: str, start: int, end: int | None = None) -> BinaryIO:
        """Récupère une plage inclusive d'un objet."""

    @abstractmethod
    async def head(self, key: str) -> ObjectMetadata:
        """Retourne les métadonnées de l'objet."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Supprime un objet."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Vérifie si un objet existe."""

    @abstractmethod
    async def get_presigned_url(
        self, key: str, expires_in: int = _DEFAULT_PRESIGNED_EXPIRES
    ) -> str:
        """Génère une URL présignée pour téléchargement temporaire."""

    async def close(self) -> None:
        """Libère les ressources réseau ; sans effet pour le backend local."""
        return None


class LocalStorage(ObjectStorage):
    """Stockage filesystem local — dev uniquement."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve_key(self, key: str) -> Path:
        """Résout une clé sans autoriser une sortie du répertoire configuré."""
        normalized = _validate_key(key)
        candidate = (self._base / normalized).resolve()
        if candidate == self._base or not candidate.is_relative_to(self._base):
            raise ValueError("Object key resolves outside configured storage")
        return candidate

    async def put(
        self, key: str, data: BinaryIO, content_type: str = "application/octet-stream"
    ) -> str:
        path = self._resolve_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(self._write_file, path, data)
        logger.info("object_stored_local", key_fingerprint=_key_fingerprint(key))
        # L'URI persistée est un identifiant interne, jamais un chemin du
        # système de fichiers. Le téléchargement local doit passer par le
        # service autorisé qui connaît déjà la clé, pas par une URI `file://`.
        return f"local:///{quote(_validate_key(key), safe='/')}"

    @staticmethod
    def _write_file(path: Path, data: BinaryIO) -> None:
        with path.open("wb") as target:
            while chunk := data.read(_DEFAULT_CHUNK_SIZE):
                target.write(chunk)

    async def get(self, key: str, start: int | None = None, end: int | None = None) -> BinaryIO:
        path = self._resolve_key(key)
        self._validate_range(start, end)
        if start is None and end is not None:
            start = 0
        result = tempfile.SpooledTemporaryFile(  # noqa: SIM115 - retourné au caller
            max_size=_DEFAULT_CHUNK_SIZE, mode="w+b"
        )
        try:
            with path.open("rb") as source:
                if start is not None:
                    source.seek(start)
                remaining = None if start is None or end is None else end - start + 1
                read_size = _DEFAULT_CHUNK_SIZE
                while chunk := source.read(
                    read_size if remaining is None else min(remaining, read_size)
                ):
                    result.write(chunk)
                    if remaining is not None:
                        remaining -= len(chunk)
                        if remaining <= 0:
                            break
        except BaseException:
            result.close()
            raise
        result.seek(0)
        return cast(BinaryIO, result)

    async def get_stream(
        self,
        key: str,
        start: int | None = None,
        end: int | None = None,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> AsyncIterator[bytes]:
        path = self._resolve_key(key)
        self._validate_range(start, end)
        if start is None and end is not None:
            start = 0
        _validate_read_chunk_size(chunk_size)
        with path.open("rb") as source:
            if start is not None:
                source.seek(start)
            remaining = None if start is None or end is None else end - start + 1
            while remaining != 0:
                length = chunk_size if remaining is None else min(remaining, chunk_size)
                chunk = await asyncio.to_thread(source.read, length)
                if not chunk:
                    break
                yield chunk
                if remaining is not None:
                    remaining -= len(chunk)

    def iter_chunks(self, key: str, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> AsyncIterator[bytes]:
        _validate_read_chunk_size(chunk_size)
        return self.get_stream(key, chunk_size=chunk_size)

    async def get_range(self, key: str, start: int, end: int | None = None) -> BinaryIO:
        return await self.get(key, start=start, end=end)

    async def head(self, key: str) -> ObjectMetadata:
        path = self._resolve_key(key)
        stat = path.stat()
        return {"content_length": stat.st_size, "metadata": {}}

    async def delete(self, key: str) -> bool:
        path = self._resolve_key(key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._resolve_key(key).exists()

    async def get_presigned_url(
        self, key: str, expires_in: int = _DEFAULT_PRESIGNED_EXPIRES
    ) -> str:
        _validate_expires(expires_in)
        self._resolve_key(key)
        raise ObjectStorageError(
            "URL présignée indisponible avec le stockage local ; "
            "utilisez un téléchargement API autorisé"
        )

    @staticmethod
    def _validate_range(start: int | None, end: int | None) -> None:
        if start is not None and start < 0:
            raise ValueError("Range start must be non-negative")
        if end is not None and (end < 0 or (start is not None and end < start)):
            raise ValueError("Range end must be greater than or equal to start")


class S3Storage(ObjectStorage):
    """Stockage S3-compatible (MinIO, AWS S3, Scaleway)."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
        server_side_encryption: str | None = None,
        multipart_chunk_size: int = 8 * 1024 * 1024,
        session: AioSession | None = None,
    ) -> None:
        if not endpoint.strip() or not access_key or not secret_key or not bucket.strip():
            raise ValueError("S3 endpoint, credentials and bucket are required")
        _validate_chunk_size(multipart_chunk_size)
        self._endpoint = endpoint.rstrip("/")
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region
        self._server_side_encryption = server_side_encryption
        self._multipart_chunk_size = multipart_chunk_size
        self._session = session or get_session()
        self._client_lock = asyncio.Lock()
        self._client_context: Any | None = None
        self._shared_client: Any | None = None

    async def _get_client(self) -> Any:
        """Ouvre une fois le client aiobotocore et réutilise son pool HTTP."""
        if self._shared_client is not None:
            return self._shared_client
        async with self._client_lock:
            if self._shared_client is None:
                context = self._session.create_client(
                    "s3",
                    endpoint_url=self._endpoint,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    region_name=self._region,
                )
                client = await context.__aenter__()
                self._client_context = context
                self._shared_client = client
        return self._shared_client

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[Any]:
        yield await self._get_client()

    async def close(self) -> None:
        """Ferme une seule fois le client partagé et son pool de connexions."""
        async with self._client_lock:
            context = self._client_context
            self._client_context = None
            self._shared_client = None
        if context is not None:
            await context.__aexit__(None, None, None)

    def _uri(self, key: str) -> str:
        return f"s3://{self._bucket}/{quote(key, safe='/')}"

    async def put(
        self, key: str, data: BinaryIO, content_type: str = "application/octet-stream"
    ) -> str:
        normalized = _validate_key(key)
        with tempfile.SpooledTemporaryFile(
            max_size=self._multipart_chunk_size, mode="w+b"
        ) as staged:
            digest, size = await asyncio.to_thread(
                _copy_and_hash, data, cast(BinaryIO, staged), self._multipart_chunk_size
            )
            staged.seek(0)
            try:
                async with self._client() as client:
                    await self._upload(
                        client, normalized, cast(BinaryIO, staged), digest, size, content_type
                    )
            except Exception as exc:
                raise _translate_error("put", normalized, exc) from exc
        return self._uri(normalized)

    async def _upload(
        self,
        client: Any,
        key: str,
        staged: BinaryIO,
        digest: str,
        size: int,
        content_type: str,
    ) -> None:
        metadata = {"sha256": digest}
        encryption = (
            {"ServerSideEncryption": self._server_side_encryption}
            if self._server_side_encryption
            else {}
        )
        if size == 0:
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=b"",
                ContentType=content_type,
                Metadata=metadata,
                **encryption,
            )
            return
        response = await client.create_multipart_upload(
            Bucket=self._bucket,
            Key=key,
            ContentType=content_type,
            Metadata=metadata,
            **encryption,
        )
        upload_id = str(response["UploadId"])
        try:
            parts = await self._upload_parts(client, key, upload_id, staged)
            await client.complete_multipart_upload(
                Bucket=self._bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
        except BaseException:
            await self._abort_upload(client, key, upload_id)
            raise

    async def _upload_parts(
        self, client: Any, key: str, upload_id: str, staged: BinaryIO
    ) -> list[dict[str, object]]:
        parts: list[dict[str, object]] = []
        part_number = 1
        while chunk := await asyncio.to_thread(staged.read, self._multipart_chunk_size):
            response = await client.upload_part(
                Bucket=self._bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=chunk,
            )
            parts.append({"ETag": str(response["ETag"]), "PartNumber": part_number})
            part_number += 1
        return parts

    async def _abort_upload(self, client: Any, key: str, upload_id: str) -> None:
        try:
            await client.abort_multipart_upload(Bucket=self._bucket, Key=key, UploadId=upload_id)
        except Exception as exc:
            logger.error(
                "object_storage_abort_failed",
                key_fingerprint=_key_fingerprint(key),
                error_type=type(exc).__name__,
            )

    async def get(self, key: str, start: int | None = None, end: int | None = None) -> BinaryIO:
        normalized = _validate_key(key)
        self._validate_range(start, end)
        if start is None and end is not None:
            start = 0
        result = tempfile.SpooledTemporaryFile(  # noqa: SIM115 - retourné au caller
            max_size=self._multipart_chunk_size, mode="w+b"
        )
        try:
            async for chunk in self.get_stream(normalized, start=start, end=end):
                result.write(chunk)
        except BaseException:
            result.close()
            raise
        result.seek(0)
        return cast(BinaryIO, result)

    async def get_stream(
        self,
        key: str,
        start: int | None = None,
        end: int | None = None,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> AsyncIterator[bytes]:
        normalized = _validate_key(key)
        self._validate_range(start, end)
        if start is None and end is not None:
            start = 0
        _validate_read_chunk_size(chunk_size)
        request: dict[str, object] = {"Bucket": self._bucket, "Key": normalized}
        if start is not None:
            request["Range"] = f"bytes={start}-{'' if end is None else end}"
        try:
            async with self._client() as client:
                response = await client.get_object(**request)
                body = response["Body"]
                try:
                    while chunk := await body.read(chunk_size):
                        yield cast(bytes, chunk)
                finally:
                    await _close_body(body)
        except Exception as exc:
            raise _translate_error("get", normalized, exc) from exc

    def iter_chunks(self, key: str, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> AsyncIterator[bytes]:
        _validate_read_chunk_size(chunk_size)
        return self.get_stream(key, chunk_size=chunk_size)

    async def get_range(self, key: str, start: int, end: int | None = None) -> BinaryIO:
        return await self.get(key, start=start, end=end)

    async def head(self, key: str) -> ObjectMetadata:
        normalized = _validate_key(key)
        try:
            async with self._client() as client:
                response = await client.head_object(Bucket=self._bucket, Key=normalized)
                return cast(ObjectMetadata, dict(response))
        except Exception as exc:
            raise _translate_error("head", normalized, exc) from exc

    async def delete(self, key: str) -> bool:
        normalized = _validate_key(key)
        try:
            async with self._client() as client:
                await client.delete_object(Bucket=self._bucket, Key=normalized)
        except Exception as exc:
            raise _translate_error("delete", normalized, exc) from exc
        return True

    async def exists(self, key: str) -> bool:
        normalized = _validate_key(key)
        try:
            await self.head(normalized)
        except ObjectNotFoundError:
            return False
        return True

    async def get_presigned_url(
        self, key: str, expires_in: int = _DEFAULT_PRESIGNED_EXPIRES
    ) -> str:
        normalized = _validate_key(key)
        _validate_expires(expires_in)
        try:
            async with self._client() as client:
                result = client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self._bucket, "Key": normalized},
                    ExpiresIn=expires_in,
                )
                if inspect.isawaitable(result):
                    result = await result
                return cast(str, result)
        except Exception as exc:
            raise _translate_error("presigned_url", normalized, exc) from exc

    @staticmethod
    def _validate_range(start: int | None, end: int | None) -> None:
        if start is not None and start < 0:
            raise ValueError("Range start must be non-negative")
        if end is not None and (end < 0 or (start is not None and end < start)):
            raise ValueError("Range end must be greater than or equal to start")


def _validate_chunk_size(chunk_size: int) -> None:
    if chunk_size < _MIN_MULTIPART_CHUNK_SIZE:
        raise ValueError("Multipart chunk size must be at least 5 MiB")


def _validate_read_chunk_size(chunk_size: int) -> None:
    if chunk_size < 1:
        raise ValueError("Read chunk size must be positive")


def _validate_expires(expires_in: int) -> None:
    if expires_in < 1 or expires_in > _MAX_PRESIGNED_EXPIRES:
        raise ValueError("Presigned URL expiration must be between 1 second and 15 minutes")


_object_storage_instance: ObjectStorage | None = None


def get_object_storage() -> ObjectStorage:
    """Factory — retourne le storage selon la configuration."""
    global _object_storage_instance

    if _object_storage_instance is not None:
        return _object_storage_instance
    if _settings.object_storage_backend == "local":
        if _settings.environment in ("staging", "production"):
            raise RuntimeError("S3 object storage is required outside development")
        _object_storage_instance = LocalStorage(_settings.object_storage_local_path)
    else:
        _object_storage_instance = S3Storage(
            endpoint=_settings.object_storage_s3_endpoint or "",
            access_key=_settings.object_storage_s3_access_key.get_secret_value(),
            secret_key=_settings.object_storage_s3_secret_key.get_secret_value(),
            bucket=_settings.object_storage_s3_bucket,
            region=_settings.object_storage_s3_region,
            server_side_encryption=_settings.object_storage_s3_server_side_encryption,
            multipart_chunk_size=_settings.object_storage_s3_multipart_chunk_size,
        )
    return _object_storage_instance


async def close_object_storage() -> None:
    """Ferme le singleton de stockage au shutdown et autorise un redémarrage."""
    global _object_storage_instance

    storage = _object_storage_instance
    _object_storage_instance = None
    if storage is not None:
        await storage.close()
