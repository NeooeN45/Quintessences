"""Tests d'intégration — Pedology Engine.

Pas de dépendance à Postgres (v1 sans persistance, voir docstring
engine.py) — les appels à SoilGrids sont mockés via respx avec la
forme de réponse réelle (vérifiée manuellement contre rest.isric.org
le 2026-07-17, lon=1.0/lat=44.0, France) — pas de donnée inventée.
"""

import pytest
import respx
from httpx import Response

from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError
from gsie_api.engines.pedology.schemas import PedologyQuery
from gsie_api.engines.pedology.soilgrids_client import (
    _SOILGRIDS_URL,
    SoilGridsClient,
    SoilGridsClientError,
)

# Réponse réelle capturée (rest.isric.org, lon=1.0, lat=44.0, 2026-07-17).
_REAL_RESPONSE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [1.0, 44.0]},
    "properties": {
        "layers": [
            {
                "name": "clay",
                "unit_measure": {"d_factor": 10, "mapped_units": "g/kg", "target_units": "%"},
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 283},
                    }
                ],
            },
            {
                "name": "phh2o",
                "unit_measure": {"d_factor": 10, "mapped_units": "pH*10", "target_units": "-"},
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 69},
                    }
                ],
            },
            {
                "name": "sand",
                "unit_measure": {"d_factor": 10, "mapped_units": "g/kg", "target_units": "%"},
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 233},
                    }
                ],
            },
            {
                "name": "silt",
                "unit_measure": {"d_factor": 10, "mapped_units": "g/kg", "target_units": "%"},
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 483},
                    }
                ],
            },
        ]
    },
    "query_time_s": 1.0,
}

_NULL_RESPONSE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
    "properties": {
        "layers": [
            {
                "name": "phh2o",
                "unit_measure": {"d_factor": 10, "mapped_units": "pH*10", "target_units": "-"},
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": None},
                    }
                ],
            }
        ]
    },
}


@pytest.fixture
def engine() -> PedologyEngine:
    return PedologyEngine(soilgrids_client=SoilGridsClient())


@respx.mock
async def test_query_returns_real_scaled_values(engine: PedologyEngine):
    """Les valeurs retournées doivent être mises à l'échelle par d_factor (pH=6.9, argile=28.3%)."""
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(200, json=_REAL_RESPONSE))

    result = await engine.query(PedologyQuery(latitude=44.0, longitude=1.0))

    by_nom = {c.nom: c.valeur for c in result.caracteristiques}
    assert by_nom["ph"] == pytest.approx(6.9)
    assert by_nom["argile_pct"] == pytest.approx(28.3)
    assert by_nom["sable_pct"] == pytest.approx(23.3)
    assert by_nom["limon_pct"] == pytest.approx(48.3)
    # argile + sable + limon doivent sommer à ~100% (vérification de cohérence physique)
    assert by_nom["argile_pct"] + by_nom["sable_pct"] + by_nom["limon_pct"] == pytest.approx(
        99.9, abs=0.1
    )


@respx.mock
async def test_query_evidence_level_is_b_not_a(engine: PedologyEngine):
    """SoilGrids est une source unique peer-reviewed — plafond B, jamais A."""
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(200, json=_REAL_RESPONSE))

    result = await engine.query(PedologyQuery(latitude=44.0, longitude=1.0))

    assert all(c.evidence_level.value == "B" for c in result.caracteristiques)
    assert all(c.source.auteur == "Poggio, L. et al." for c in result.caracteristiques)


@respx.mock
async def test_query_omits_properties_without_coverage(engine: PedologyEngine):
    """Une propriété sans donnée (mean=null) doit être omise — jamais une valeur par défaut."""
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(200, json=_NULL_RESPONSE))

    result = await engine.query(PedologyQuery(latitude=0.0, longitude=0.0))

    assert result.caracteristiques == []


@respx.mock
async def test_query_raises_on_soilgrids_api_failure(engine: PedologyEngine):
    """Une panne de l'API SoilGrids doit lever PedologyEngineError."""
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(503))

    with pytest.raises(PedologyEngineError):
        await engine.query(PedologyQuery(latitude=44.0, longitude=1.0))


async def test_soilgrids_client_raises_on_network_error():
    """Une erreur HTTP doit lever SoilGridsClientError, pas une exception générique."""
    client = SoilGridsClient()
    with respx.mock:
        respx.get(_SOILGRIDS_URL).mock(return_value=Response(500))
        with pytest.raises(SoilGridsClientError):
            await client.get_properties(44.0, 1.0, ["phh2o"])


def test_return_engine_version():
    """version() doit retourner une chaîne non vide."""
    assert len(PedologyEngine.version()) > 0
