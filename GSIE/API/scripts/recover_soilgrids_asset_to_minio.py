"""Transfère vers MinIO le micro-extrait déjà validé, sans nouvel appel fournisseur."""

from __future__ import annotations

import asyncio
import hashlib
from io import BytesIO
from uuid import UUID

from sqlalchemy import select

from gsie_api.infrastructure.database import async_session_factory, engine
from gsie_api.infrastructure.models.models_ai import DataAssetModel
from gsie_api.infrastructure.object_storage import (
    LocalStorage,
    close_object_storage,
    get_object_storage,
)

_ASSET_ID = UUID("a584c377-ff39-4e58-967a-7304b732bb47")
_KEY = f"raw/fetch/soilgrids/{_ASSET_ID}.tif"


async def main() -> None:
    local = LocalStorage("./data/assets")
    remote = get_object_storage()
    async with async_session_factory() as session:
        asset = await session.scalar(select(DataAssetModel).where(DataAssetModel.id == _ASSET_ID))
        if asset is None:
            raise RuntimeError("DataAsset du micro-extrait absent")
        if asset.storage_uri is not None and asset.storage_uri.startswith("s3://"):
            print(f"minio_recovery=ALREADY_COMPLETED uri={asset.storage_uri}")
            await close_object_storage()
            await engine.dispose()
            return

    local_file = await local.get(_KEY)
    content = local_file.read()
    local_file.close()
    digest = hashlib.sha256(content).hexdigest()

    async with async_session_factory() as session:
        asset = await session.scalar(select(DataAssetModel).where(DataAssetModel.id == _ASSET_ID))
        if asset is None:
            raise RuntimeError("DataAsset du micro-extrait absent")
        if asset.checksum != digest or asset.size_bytes != len(content):
            raise RuntimeError("la copie locale diverge du reçu persisté")

    storage_uri = await remote.put(_KEY, BytesIO(content), "image/tiff")
    try:
        downloaded = await remote.get(_KEY)
        roundtrip = downloaded.read()
        downloaded.close()
        if hashlib.sha256(roundtrip).hexdigest() != digest or roundtrip != content:
            raise RuntimeError("le round-trip MinIO diverge de la copie validée")
        async with async_session_factory() as session, session.begin():
            asset = await session.scalar(
                select(DataAssetModel).where(DataAssetModel.id == _ASSET_ID).with_for_update()
            )
            if asset is None:
                raise RuntimeError("DataAsset disparu pendant la récupération")
            asset.storage_uri = storage_uri
        await local.delete(_KEY)
        print(f"minio_recovery=OK uri={storage_uri} sha256={digest} size={len(content)}")
    except BaseException:
        await remote.delete(_KEY)
        raise
    finally:
        await close_object_storage()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
