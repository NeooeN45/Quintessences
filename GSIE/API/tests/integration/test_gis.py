"""Tests d'intégration — GIS Engine (persistance PostgreSQL/PostGIS réelle).

Les appels aux API IGN sont mockés via respx avec les formes de réponse
réelles (vérifiées manuellement contre apicarto.ign.fr et
data.geopf.fr le 2026-07-17) — pas de dépendance réseau dans les tests,
mais pas de donnée inventée non plus : ces réponses sont des copies
exactes d'appels réels.
"""

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.gis.engine import GISEngine, GISEngineError
from gsie_api.engines.gis.ign_client import (
    _ALTIMETRIE_BASE_URL,
    _CADASTRE_BASE_URL,
    IGNClient,
    IGNClientError,
)
from gsie_api.engines.gis.schemas import AltitudeRequest, CoucheGeo, ParcelleCadastraleRequest
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel
from tests.conftest import requires_docker

pytestmark = requires_docker

# Réponse réelle capturée (apicarto.ign.fr, code_insee=33063, 2026-07-17) —
# une seule feature, simplifiée mais géométrie et propriétés authentiques.
_REAL_PARCELLE_FEATURE = {
    "type": "Feature",
    "id": "parcelle.9874",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [
                    [-0.5452669, 44.85137836],
                    [-0.54550705, 44.85144955],
                    [-0.54529388, 44.85158893],
                    [-0.54525057, 44.85161726],
                    [-0.54513897, 44.85158154],
                    [-0.54520949, 44.85147032],
                    [-0.54523044, 44.85143694],
                    [-0.5452669, 44.85137836],
                ]
            ]
        ],
    },
    "geometry_name": "geom",
    "properties": {
        "gid": 130644,
        "numero": "0001",
        "feuille": 1,
        "section": "AM",
        "code_dep": "33",
        "nom_com": "Bordeaux",
        "code_com": "063",
        "code_insee": "33063",
        "contenance": 376,
        "idu": "33063000AM0001",
    },
}


@pytest.fixture
def engine(db_session: AsyncSession) -> GISEngine:
    return GISEngine(db_session, ign_client=IGNClient())


@respx.mock
async def test_get_parcelle_cadastre_persists_real_geometry(
    engine: GISEngine, db_session: AsyncSession
):
    """Une parcelle trouvée doit être persistée comme resource `place` en Lambert-93."""
    respx.get(_CADASTRE_BASE_URL).mock(
        return_value=Response(
            200,
            json={"type": "FeatureCollection", "features": [_REAL_PARCELLE_FEATURE]},
        )
    )

    request = ParcelleCadastraleRequest(code_insee="33063", section="AM", numero="0001")
    result = await engine.get_parcelle_cadastre(request)

    assert result is not None
    assert result.place_id is not None
    assert result.couches[0].nom == CoucheGeo.cadastre
    assert result.source.auteur == "IGN"

    place = await db_session.get(PlaceModel, result.place_id)
    assert place is not None
    assert place.srid == 2154
    assert place.label == "33063000AM0001"
    assert place.area_m2 == 376.0


@respx.mock
async def test_get_parcelle_cadastre_returns_none_when_not_found(engine: GISEngine):
    """Aucune parcelle correspondante doit retourner None — jamais une géométrie approximée."""
    respx.get(_CADASTRE_BASE_URL).mock(
        return_value=Response(
            200,
            json={"type": "FeatureCollection", "features": [], "totalFeatures": 0},
        )
    )

    request = ParcelleCadastraleRequest(code_insee="33063", section="ZZ", numero="9999")
    result = await engine.get_parcelle_cadastre(request)

    assert result is None


@respx.mock
async def test_get_parcelle_cadastre_raises_on_ign_api_failure(engine: GISEngine):
    """Une panne de l'API Carto doit lever IGNClientError, jamais une donnée par défaut."""
    respx.get(_CADASTRE_BASE_URL).mock(return_value=Response(503))

    request = ParcelleCadastraleRequest(code_insee="33063", section="AM", numero="0001")
    with pytest.raises(IGNClientError):
        await engine.get_parcelle_cadastre(request)


@respx.mock
async def test_get_altitude_returns_real_value(engine: GISEngine):
    """L'altitude retournée correspond exactement à la réponse IGN (pas d'arrondi inventé)."""
    respx.get(_ALTIMETRIE_BASE_URL).mock(return_value=Response(200, json={"elevations": [3.9]}))

    request = AltitudeRequest(latitude=44.85137836, longitude=-0.5452669)
    result = await engine.get_altitude(request)

    assert result.altitude_m == 3.9
    assert result.source.auteur == "IGN"
    assert "RGE ALTI" in result.source.reference


@respx.mock
async def test_get_altitude_raises_on_empty_elevations(engine: GISEngine):
    """Une réponse sans élévation exploitable doit lever une erreur, pas 0.0 par défaut."""
    respx.get(_ALTIMETRIE_BASE_URL).mock(return_value=Response(200, json={"elevations": []}))

    request = AltitudeRequest(latitude=0.0, longitude=0.0)
    with pytest.raises(GISEngineError):
        await engine.get_altitude(request)


@respx.mock
async def test_get_altitude_raises_on_ign_api_failure(engine: GISEngine):
    """Une panne de l'API altimétrique doit lever GISEngineError."""
    respx.get(_ALTIMETRIE_BASE_URL).mock(return_value=Response(500))

    request = AltitudeRequest(latitude=44.0, longitude=-0.5)
    with pytest.raises(GISEngineError):
        await engine.get_altitude(request)


def test_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(GISEngine.version()) > 0
