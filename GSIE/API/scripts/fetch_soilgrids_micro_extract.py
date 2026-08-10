"""Exécute l'unique micro-FETCH SoilGrids autorisé le 10 août 2026."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx
from sqlalchemy import select

from gsie_api.data.adapters import (
    AdapterCapability,
    AdapterContext,
    AdapterDescriptor,
    AdapterFetchRequest,
    AdapterFetchResult,
    DataSourceAdapter,
)
from gsie_api.data.fetch_policy import (
    FetchQualificationRegistry,
    FetchQualificationStatus,
    FetchSourceQualification,
)
from gsie_api.data.fetch_sink import TransactionalObjectStorageSink
from gsie_api.data.fetch_worker import BoundedFetchWorker
from gsie_api.data.soilgrids_wcs_policy import (
    SOILGRIDS_FETCH_MAX_BYTES,
    SOILGRIDS_FETCH_TIMEOUT_SECONDS,
    SOILGRIDS_WCS_ENDPOINT,
    SoilGridsWcsRequest,
)
from gsie_api.infrastructure.database import async_session_factory, engine
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.models_ai import (
    DataAssetModel,
    DatasetModel,
    DatasetVersionModel,
)
from gsie_api.infrastructure.object_storage import close_object_storage, get_object_storage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_PIXEL_LIMIT = 10_000
_BBOX = (-1_463_750.0, 1_608_250.0, -1_461_250.0, 1_610_750.0)
_CONTENT_TYPE = "image/tiff"
_DECISION_CONSUMED = True


class _SingleUseSoilGridsWcsAdapter(DataSourceAdapter):
    """Adapter fermé sur une URL canonique unique pour cette preuve opérateur."""

    def __init__(self, allowed_url: str) -> None:
        self._allowed_url = allowed_url
        self._descriptor = AdapterDescriptor(
            key="soilgrids-wcs-single-use",
            name="SoilGrids WCS — preuve opérateur unique",
            version="1.0.0",
            capabilities=frozenset({AdapterCapability.FETCH, AdapterCapability.HEALTH}),
            domains=frozenset({"pedology"}),
            endpoint=SOILGRIDS_WCS_ENDPOINT,
            allowlisted_hosts=frozenset({"maps.isric.org"}),
        )

    @property
    def descriptor(self) -> AdapterDescriptor:
        return self._descriptor

    def validate_target_url(self, url: str) -> str:
        normalized = super().validate_target_url(url)
        if normalized != SOILGRIDS_WCS_ENDPOINT:
            raise ValueError("la sonde opérateur refuse tout autre endpoint WCS")
        return normalized

    async def fetch(
        self, request: AdapterFetchRequest, context: AdapterContext
    ) -> AdapterFetchResult:
        if context.offline:
            raise ValueError("FETCH impossible en mode hors ligne")
        client = httpx.AsyncClient(follow_redirects=False, verify=True)
        response = await client.send(client.build_request("GET", self._allowed_url), stream=True)
        try:
            response.raise_for_status()
        except BaseException:
            await response.aclose()
            await client.aclose()
            raise

        async def body() -> AsyncIterator[bytes]:
            try:
                async for chunk in response.aiter_bytes(64 * 1024):
                    yield chunk
            finally:
                await response.aclose()
                await client.aclose()

        length = response.headers.get("content-length")
        return AdapterFetchResult(
            body=body(),
            content_type=response.headers.get("content-type"),
            content_length=int(length) if length is not None else None,
        )


def _canonical_url(request: SoilGridsWcsRequest) -> str:
    params: list[tuple[str, str]] = []
    for key, value in request.parameters.items():
        if isinstance(value, tuple):
            params.extend((key, item) for item in value)
        else:
            params.append((key, value))
    return str(httpx.URL(SOILGRIDS_WCS_ENDPOINT, params=params))


async def main() -> None:
    if _DECISION_CONSUMED:
        raise RuntimeError(
            "DEC-000061 est consommée : ce script historique ne doit jamais être rejoué"
        )
    wcs_request = SoilGridsWcsRequest("bdod", "0-5cm", "mean", _BBOX)
    if wcs_request.estimated_pixels > _PIXEL_LIMIT:
        raise RuntimeError("la sonde dépasse 10 000 pixels")
    url = _canonical_url(wcs_request)
    now = datetime.now(UTC)
    qualifications = FetchQualificationRegistry(
        schema_version="1",
        generated_at=date.today(),
        sources=[
            FetchSourceQualification(
                source_registry_id="soilgrids",
                status=FetchQualificationStatus.qualified,
                fetch_enabled=True,
                legal_basis="SCI-001:OPEN_COPY",
                evidence_refs=["DECISION_OPERATEUR_2026-08-10", "SCI-001", "RFC-0038"],
                allowed_hosts=["maps.isric.org"],
                allowed_content_types=[_CONTENT_TYPE],
                max_bytes=SOILGRIDS_FETCH_MAX_BYTES,
                checksum_algorithm="sha256",
                reviewed_by="Fondateur Quintessences",
                reviewed_at=now,
            )
        ],
    )
    storage = get_object_storage()
    asset_id = uuid4()
    final_key = f"raw/fetch/soilgrids/{asset_id}.tif"
    sink = TransactionalObjectStorageSink(
        storage,
        final_key=final_key,
        content_type=_CONTENT_TYPE,
        spool_max_bytes=SOILGRIDS_FETCH_MAX_BYTES,
    )
    worker = BoundedFetchWorker(qualifications)
    try:
        receipt = await worker.fetch(
            source_registry_id="soilgrids",
            adapter=_SingleUseSoilGridsWcsAdapter(url),
            request=AdapterFetchRequest(
                external_id=wcs_request.coverage_id,
                distribution_url=SOILGRIDS_WCS_ENDPOINT,
                max_bytes=SOILGRIDS_FETCH_MAX_BYTES,
            ),
            context=AdapterContext(
                trace_id=f"soilgrids-micro-{asset_id.hex[:12]}",
                timeout_seconds=SOILGRIDS_FETCH_TIMEOUT_SECONDS,
                max_bytes=SOILGRIDS_FETCH_MAX_BYTES,
            ),
            sink=sink,
        )
        if sink.storage_uri is None:
            raise RuntimeError("publication RAW absente après commit")
        async with async_session_factory() as session, session.begin():
            version_id = await session.scalar(
                select(DatasetVersionModel.id)
                .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
                .where(DatasetModel.slug == "soilgrids-properties")
                .order_by(DatasetVersionModel.created_at.desc())
                .limit(1)
            )
            if version_id is None:
                raise RuntimeError("version SoilGrids absente du Data Registry")
            session.add(
                ResourceModel(
                    id=asset_id,
                    type="data_asset",
                    gsie_id=f"DA-SOILGRIDS-{asset_id.hex[:16]}",
                    metadata_json={
                        "stage": "RAW",
                        "promotion_automatic": False,
                        "coverage_id": wcs_request.coverage_id,
                        "bbox": list(_BBOX),
                        "estimated_pixels": wcs_request.estimated_pixels,
                    },
                )
            )
            session.add(
                DataAssetModel(
                    id=asset_id,
                    dataset_version_id=version_id,
                    format="GEOTIFF_INT16",
                    size_bytes=receipt.size_bytes,
                    checksum=receipt.checksum_sha256,
                    original_uri=SOILGRIDS_WCS_ENDPOINT,
                    storage_uri=sink.storage_uri,
                    checksum_algorithm="sha256",
                    archived_at=now,
                )
            )
        print(
            json.dumps(
                {
                    "data_asset_id": str(asset_id),
                    "coverage_id": wcs_request.coverage_id,
                    "estimated_pixels": wcs_request.estimated_pixels,
                    "size_bytes": receipt.size_bytes,
                    "sha256": receipt.checksum_sha256,
                    "content_type": receipt.content_type,
                    "storage_uri": sink.storage_uri,
                    "promotion": "AUCUNE",
                },
                indent=2,
            )
        )
    except BaseException:
        if sink.storage_uri is not None:
            await storage.delete(final_key)
        raise
    finally:
        await close_object_storage()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
