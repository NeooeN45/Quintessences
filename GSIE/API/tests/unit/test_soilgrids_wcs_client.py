"""Tests hors réseau du client HTTP WCS SoilGrids."""

from io import BytesIO

import httpx
import numpy as np
import pytest
import rasterio
import respx
from httpx import Response
from rasterio.transform import from_bounds

from gsie_api.data.adapters import AdapterSecurityError
from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClient, SoilGridsWcsClientError
from gsie_api.data.soilgrids_wcs_policy import (
    SOILGRIDS_WCS_ENDPOINT,
    SOILGRIDS_WCS_PROJ4,
    SoilGridsWcsRequest,
)
from gsie_api.shared import http_client


def _request() -> SoilGridsWcsRequest:
    return SoilGridsWcsRequest(
        property_code="wv003",
        depth="5-15cm",
        quantile="Q0.5",
        bbox=(-500.0, 1000.0, 0.0, 1500.0),
    )


def _geotiff(
    bbox: tuple[float, float, float, float],
    raw_value: int | float,
    *,
    dtype: str = "int16",
    nodata: int | float | None = None,
) -> bytes:
    """Crée une petite couverture GeoTIFF représentative d'une réponse WCS."""

    buffer = BytesIO()
    profile: dict[str, object] = {
        "driver": "GTiff",
        "height": 1,
        "width": 1,
        "count": 1,
        "dtype": dtype,
        "crs": SOILGRIDS_WCS_PROJ4,
        "transform": from_bounds(*bbox, 1, 1),
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(buffer, mode="w", **profile) as dataset:
        dataset.write(np.array([[raw_value]], dtype=dtype), 1)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _stub_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_client, "_dns_resolver", lambda hostname: ["8.8.8.8"])


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_probe_utilise_get_capabilities_sans_getcoverage() -> None:
    route = respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=httpx.Response(200, content=b"<WCS_Capabilities/>")
    )

    await SoilGridsWcsClient().probe()

    assert route.called
    assert route.calls[0].request.url.params.get("REQUEST") == "GetCapabilities"


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_retourne_un_flux_et_les_entetes_fournisseur() -> None:
    payload = b"geotiff-wcs"
    route = respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=httpx.Response(200, content=payload, headers={"content-type": "image/tiff"})
    )

    result = await SoilGridsWcsClient().fetch_coverage(
        _request(), timeout_seconds=30.0, max_bytes=8 * 1024 * 1024
    )

    assert result.content_type == "image/tiff"
    assert result.content_length == len(payload)
    assert b"".join([chunk async for chunk in result.body]) == payload
    requested_url = str(route.calls[0].request.url)
    assert "SERVICE=WCS" in requested_url
    assert "COVERAGEID=wv0033_5-15cm_Q0.5" in requested_url
    assert (
        "SUBSETTINGCRS=http%3A%2F%2Fwww.opengis.net%2Fdef%2Fcrs%2FEPSG%2F0%2F152160"
        in requested_url
    )


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_refuse_un_content_length_malforme() -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            content=b"geotiff-wcs",
            headers={"content-type": "image/tiff", "content-length": "not-a-number"},
        )
    )

    with pytest.raises(SoilGridsWcsClientError, match="Content-Length"):
        await SoilGridsWcsClient().fetch_coverage(
            _request(), timeout_seconds=30.0, max_bytes=8 * 1024 * 1024
        )


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_refuse_un_flux_superieur_a_la_borne() -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            content=b"geotiff-wcs",
            headers={"content-type": "image/tiff", "content-length": "11"},
        )
    )

    with pytest.raises(AdapterSecurityError, match="SIZE_LIMIT"):
        await SoilGridsWcsClient().fetch_coverage(_request(), timeout_seconds=30.0, max_bytes=10)


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_lit_et_convertit_les_valeurs_ponctuelles() -> None:
    client = SoilGridsWcsClient()
    bbox = client._point_bbox(44.0, -0.6)
    raw_values = {"phh2o": 52, "clay": 283, "sand": 233, "silt": 483}

    def response(request: httpx.Request) -> Response:
        property_code = request.url.params["COVERAGEID"].split("_", maxsplit=1)[0]
        return Response(
            200,
            content=_geotiff(bbox, raw_values[property_code]),
            headers={"content-type": "image/tiff"},
        )

    route = respx.get(SOILGRIDS_WCS_ENDPOINT).mock(side_effect=response)

    values = await client.query_properties(
        44.0,
        -0.6,
        ["phh2o", "clay", "sand", "silt"],
    )

    assert values["phh2o"] == pytest.approx(5.2)
    assert values["clay"] == pytest.approx(28.3)
    assert values["sand"] == pytest.approx(23.3)
    assert values["silt"] == pytest.approx(48.3)
    assert route.call_count == 4
    assert all(call.request.url.params["REQUEST"] == "GetCoverage" for call in route.calls)


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_omet_une_cellule_nodata() -> None:
    client = SoilGridsWcsClient()
    bbox = client._point_bbox(44.0, -0.6)
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=Response(
            200,
            content=_geotiff(bbox, -32768, nodata=-32768),
            headers={"content-type": "image/tiff"},
        )
    )

    assert await client.query_properties(44.0, -0.6, ["phh2o"]) == {}


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_refuse_un_type_geotiff_different_de_int16() -> None:
    client = SoilGridsWcsClient()
    bbox = client._point_bbox(44.0, -0.6)
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=Response(
            200,
            content=_geotiff(bbox, 52.0, dtype="float32"),
            headers={"content-type": "image/tiff"},
        )
    )

    with pytest.raises(SoilGridsWcsClientError, match="INT16"):
        await client.query_properties(44.0, -0.6, ["phh2o"])


@pytest.mark.asyncio
@respx.mock
async def test_wcs_client_refuse_un_geotiff_invalide() -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(return_value=Response(200, content=b"pas-un-geotiff"))

    with pytest.raises(SoilGridsWcsClientError, match="GeoTIFF"):
        await SoilGridsWcsClient().query_properties(44.0, -0.6, ["phh2o"])


@pytest.mark.asyncio
async def test_wcs_client_refuse_une_propriete_non_qualifiee() -> None:
    with pytest.raises(SoilGridsWcsClientError, match="allowlist"):
        await SoilGridsWcsClient().query_properties(44.0, -0.6, ["inventee"])
