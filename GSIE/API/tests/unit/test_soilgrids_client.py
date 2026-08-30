"""Tests de compatibilité de l'ancien nom de client SoilGrids.

Le module historique reste importable pour les intégrations externes, mais
son backend est exclusivement le WCS ISRIC et son flux GeoTIFF qualifié.
"""

from __future__ import annotations

from io import BytesIO

import httpx
import numpy as np
import pytest
import rasterio
import respx
from rasterio.transform import from_bounds

from gsie_api.data.soilgrids_wcs_client import SoilGridsWcsClient
from gsie_api.data.soilgrids_wcs_policy import (
    SOILGRIDS_WCS_ENDPOINT,
    SOILGRIDS_WCS_PROJ4,
)
from gsie_api.engines.pedology.soilgrids_client import (
    _SOILGRIDS_URL,
    SoilGridsClient,
    SoilGridsClientError,
)
from gsie_api.shared import http_client


def _geotiff(raw_value: int, *, dtype: str = "int16") -> bytes:
    """Crée une couverture d'une cellule centrée sur le point de test."""

    bbox = SoilGridsWcsClient._point_bbox(44.0, -0.6)
    buffer = BytesIO()
    with rasterio.open(
        buffer,
        mode="w",
        driver="GTiff",
        height=1,
        width=1,
        count=1,
        dtype=dtype,
        crs=SOILGRIDS_WCS_PROJ4,
        transform=from_bounds(*bbox, 1, 1),
    ) as dataset:
        dataset.write(np.array([[raw_value]], dtype=dtype), 1)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _stub_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Évite toute résolution DNS pendant les tests hors réseau."""

    monkeypatch.setattr(http_client, "_dns_resolver", lambda hostname: ["8.8.8.8"])


def test_lancien_nom_pointe_vers_le_wcs_qualifie() -> None:
    """La constante historique ne doit plus contenir l'endpoint REST bêta."""

    assert _SOILGRIDS_URL == SOILGRIDS_WCS_ENDPOINT
    assert "rest.isric.org" not in _SOILGRIDS_URL


@pytest.mark.asyncio
@respx.mock
async def test_lancien_client_delegue_au_wcs_et_convertit_la_valeur() -> None:
    route = respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=httpx.Response(
            200, content=_geotiff(52), headers={"content-type": "image/tiff"}
        )
    )

    result = await SoilGridsClient().get_properties(44.0, -0.6, ["phh2o"])

    assert result == {"phh2o": pytest.approx(5.2)}
    assert "SERVICE=WCS" in str(route.calls[0].request.url)
    assert "rest.isric.org" not in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_lancien_client_preserve_son_exception_metier_sur_erreur_http() -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(return_value=httpx.Response(503))

    with pytest.raises(SoilGridsClientError):
        await SoilGridsClient().get_properties(44.0, -0.6, ["phh2o"])


@pytest.mark.asyncio
@respx.mock
async def test_lancien_client_refuse_un_geotiff_malforme() -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        return_value=httpx.Response(200, content=b"pas-un-geotiff")
    )

    with pytest.raises(SoilGridsClientError, match="GeoTIFF"):
        await SoilGridsClient().get_properties(44.0, -0.6, ["phh2o"])


def test_lancien_client_expose_les_unites_du_wcs() -> None:
    assert SoilGridsClient.unit_for("phh2o") == "pH"
    assert SoilGridsClient.unit_for("clay") == "%"
