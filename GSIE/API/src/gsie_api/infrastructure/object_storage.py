"""Object Storage abstraction (ADR-006) — S3/MinIO/local.

Abstraction unifiée pour stocker et récupérer les DataAssets
(fichiers NetCDF, GeoTIFF, LAZ, Parquet). En dev : filesystem local.
En prod : S3-compatible (MinIO, AWS S3, Scaleway).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger

logger = get_logger("gsie_api.infrastructure.object_storage")
_settings = get_settings()


class ObjectStorage(ABC):
    """Interface abstraite pour le stockage objet."""

    @abstractmethod
    async def put(self, key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        """Stocke un objet et retourne son URI."""

    @abstractmethod
    async def get(self, key: str) -> BinaryIO:
        """Récupère un objet."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Supprime un objet."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Vérifie si un objet existe."""

    @abstractmethod
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Génère une URL présignée pour téléchargement temporaire."""


class LocalStorage(ObjectStorage):
    """Stockage filesystem local — dev uniquement."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(data.read())
        logger.info("object_stored_local", key=key, path=str(path))
        return f"file://{path}"

    async def get(self, key: str) -> BinaryIO:
        path = self._base / key
        return path.open("rb")

    async def delete(self, key: str) -> bool:
        path = self._base / key
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return (self._base / key).exists()

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        # En local, pas de présignature — on retourne un chemin direct
        return f"file://{self._base / key}"


class S3Storage(ObjectStorage):
    """Stockage S3-compatible (MinIO, AWS S3, Scaleway).

    Nécessite aiobotocore. Implémentation différée (Vague 2, GIS Engine).
    """

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        raise NotImplementedError("S3Storage implémenté en Vague 2 (GIS Engine)")

    async def put(self, key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        raise NotImplementedError

    async def get(self, key: str) -> BinaryIO:
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError


def get_object_storage() -> ObjectStorage:
    """Factory — retourne le storage selon la config."""
    if _settings.environment == "production":
        # En prod : S3 (implémenté en Vague 2)
        # return S3Storage(...)
        logger.warning("s3_storage_not_implemented_using_local")
        return LocalStorage(_settings.object_storage_local_path)
    return LocalStorage(_settings.object_storage_local_path)
