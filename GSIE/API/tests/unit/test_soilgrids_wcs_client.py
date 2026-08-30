"""Tests hors réseau du client HTTP WCS SoilGrids."""

import httpx
import pytest
import respx

from gsie_api.data.adapters import AdapterSecurityError
from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClient, SoilGridsWcsClientError
from gsie_api.data.soilgrids_wcs_policy import SOILGRIDS_WCS_ENDPOINT, SoilGridsWcsRequest
from gsie_api.shared import http_client


def _request() -> SoilGridsWcsRequest:
    return SoilGridsWcsRequest(
        property_code="wv003",
        depth="5-15cm",
        quantile="Q0.5",
        bbox=(-500.0, 1000.0, 0.0, 1500.0),
    )


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
