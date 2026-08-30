"""Tests d'intégration hors réseau du Pedology Engine sur SoilGrids WCS.

Les réponses sont des GeoTIFF INT16 construits avec la projection et la
structure attendues par le service WCS. Aucun appel au service REST bêta
n'est autorisé par ces tests.
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
from gsie_api.data.soilgrids_wcs_policy import SOILGRIDS_WCS_ENDPOINT, SOILGRIDS_WCS_PROJ4
from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError
from gsie_api.engines.pedology.schemas import PedologyQuery
from gsie_api.engines.pedology.soilgrids_client import SoilGridsClient, SoilGridsClientError


def _geotiff(
    latitude: float,
    longitude: float,
    raw_value: int,
    *,
    nodata: int | None = None,
) -> bytes:
    """Crée une couverture WCS d'une cellule centrée sur un point."""

    bbox = SoilGridsWcsClient._point_bbox(latitude, longitude)
    buffer = BytesIO()
    profile: dict[str, object] = {
        "driver": "GTiff",
        "height": 1,
        "width": 1,
        "count": 1,
        "dtype": "int16",
        "crs": SOILGRIDS_WCS_PROJ4,
        "transform": from_bounds(*bbox, 1, 1),
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(buffer, mode="w", **profile) as dataset:
        dataset.write(np.array([[raw_value]], dtype="int16"), 1)
    return buffer.getvalue()


def _wcs_response(latitude: float, longitude: float) -> object:
    """Retourne une réponse WCS dépendant de la propriété demandée."""

    raw_values = {"phh2o": 69, "clay": 283, "sand": 233, "silt": 483}

    def response(request: httpx.Request) -> httpx.Response:
        property_code = request.url.params["COVERAGEID"].split("_", maxsplit=1)[0]
        return httpx.Response(
            200,
            content=_geotiff(latitude, longitude, raw_values[property_code]),
            headers={"content-type": "image/tiff"},
        )

    return response


@pytest.fixture
def engine() -> PedologyEngine:
    return PedologyEngine(soilgrids_client=SoilGridsWcsClient())


@pytest.mark.asyncio
@respx.mock
async def test_query_returns_values_scaled_from_wcs_geotiff(engine: PedologyEngine) -> None:
    route = respx.get(SOILGRIDS_WCS_ENDPOINT).mock(side_effect=_wcs_response(44.0, 1.0))

    result = await engine.query(PedologyQuery(latitude=44.0, longitude=1.0))

    by_name = {
        characteristic.nom: characteristic.valeur for characteristic in result.caracteristiques
    }
    assert by_name["ph"] == pytest.approx(6.9)
    assert by_name["argile_pct"] == pytest.approx(28.3)
    assert by_name["sable_pct"] == pytest.approx(23.3)
    assert by_name["limon_pct"] == pytest.approx(48.3)
    assert by_name["argile_pct"] + by_name["sable_pct"] + by_name["limon_pct"] == pytest.approx(
        99.9, abs=0.1
    )
    assert route.call_count == 4
    assert all("rest.isric.org" not in str(call.request.url) for call in route.calls)


@pytest.mark.asyncio
@respx.mock
async def test_query_evidence_level_is_b_and_source_is_wcs(engine: PedologyEngine) -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(side_effect=_wcs_response(44.0, 1.0))

    result = await engine.query(PedologyQuery(latitude=44.0, longitude=1.0))

    assert all(
        characteristic.evidence_level.value == "B" for characteristic in result.caracteristiques
    )
    assert all(
        characteristic.source.auteur == "Poggio, L. et al."
        for characteristic in result.caracteristiques
    )
    assert "maps.isric.org/mapserv" in result.source.reference


@pytest.mark.asyncio
@respx.mock
async def test_query_omits_wcs_nodata_without_default(engine: PedologyEngine) -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(
        side_effect=lambda request: httpx.Response(
            200,
            content=_geotiff(0.0, 0.0, -32768, nodata=-32768),
            headers={"content-type": "image/tiff"},
        )
    )

    result = await engine.query(PedologyQuery(latitude=0.0, longitude=0.0))

    assert result.caracteristiques == []


@pytest.mark.asyncio
@respx.mock
async def test_query_raises_on_wcs_failure(engine: PedologyEngine) -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(return_value=httpx.Response(503))

    with pytest.raises(PedologyEngineError):
        await engine.query(PedologyQuery(latitude=44.0, longitude=1.0))


@pytest.mark.asyncio
@respx.mock
async def test_compatibility_client_wraps_wcs_failure() -> None:
    respx.get(SOILGRIDS_WCS_ENDPOINT).mock(return_value=httpx.Response(500))

    with pytest.raises(SoilGridsClientError):
        await SoilGridsClient().get_properties(44.0, 1.0, ["phh2o"])


def test_return_engine_version() -> None:
    assert PedologyEngine.version() == "0.2.0"
