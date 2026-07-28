"""Tests unitaires étendus — IGNClient (couverture des cas non couverts par
tests/integration/test_gis.py, qui dépend de Docker/testcontainers).

Ces tests ciblent directement `IGNClient` via `respx`, sans passer par le
GISEngine ni par une session de base de données — aucune dépendance Docker.
"""

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.gis.ign_client import (
    _ALTIMETRIE_BASE_URL,
    _CADASTRE_BASE_URL,
    IGNClient,
    IGNClientError,
)

_FEATURE_UNIQUE = {
    "type": "Feature",
    "id": "parcelle.1",
    "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
    "properties": {"code_insee": "33063", "section": "AM", "numero": "0001"},
}


class TestIGNClientInit:
    """Construction du client."""

    def test_should_use_default_timeout_when_not_specified(self) -> None:
        client = IGNClient()
        assert client._timeout == 30.0

    def test_should_use_custom_timeout_when_specified(self) -> None:
        client = IGNClient(timeout=5.0)
        assert client._timeout == 5.0


class TestGetParcelle:
    """get_parcelle() — API Carto Cadastre."""

    @respx.mock
    async def test_should_return_first_feature_when_parcelle_found(self) -> None:
        respx.get(_CADASTRE_BASE_URL).mock(
            return_value=Response(
                200, json={"type": "FeatureCollection", "features": [_FEATURE_UNIQUE]}
            )
        )
        client = IGNClient()

        result = await client.get_parcelle("33063", "AM", "0001")

        assert result == _FEATURE_UNIQUE

    @respx.mock
    async def test_should_return_none_when_no_features(self) -> None:
        respx.get(_CADASTRE_BASE_URL).mock(
            return_value=Response(200, json={"type": "FeatureCollection", "features": []})
        )
        client = IGNClient()

        result = await client.get_parcelle("33063", "ZZ", "9999")

        assert result is None

    @respx.mock
    async def test_should_raise_ign_client_error_when_http_status_failure(self) -> None:
        respx.get(_CADASTRE_BASE_URL).mock(return_value=Response(503))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_parcelle("33063", "AM", "0001")

    @respx.mock
    async def test_should_raise_ign_client_error_when_network_error(self) -> None:
        respx.get(_CADASTRE_BASE_URL).mock(side_effect=httpx.ConnectError("boom"))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_parcelle("33063", "AM", "0001")

    @respx.mock
    async def test_should_raise_ign_client_error_when_timeout(self) -> None:
        respx.get(_CADASTRE_BASE_URL).mock(side_effect=httpx.TimeoutException("timeout"))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_parcelle("33063", "AM", "0001")

    @respx.mock
    async def test_should_send_expected_query_params(self) -> None:
        route = respx.get(_CADASTRE_BASE_URL).mock(
            return_value=Response(
                200, json={"type": "FeatureCollection", "features": [_FEATURE_UNIQUE]}
            )
        )
        client = IGNClient()

        await client.get_parcelle("33063", "AM", "0001")

        request = route.calls.last.request
        assert request.url.params["code_insee"] == "33063"
        assert request.url.params["section"] == "AM"
        assert request.url.params["numero"] == "0001"


class TestGetAltitude:
    """get_altitude() — API de calcul altimétrique."""

    @respx.mock
    async def test_should_return_first_elevation_when_available(self) -> None:
        respx.get(_ALTIMETRIE_BASE_URL).mock(
            return_value=Response(200, json={"elevations": [12.3, 99.9]})
        )
        client = IGNClient()

        result = await client.get_altitude(44.85, -0.54)

        assert result == 12.3

    @respx.mock
    async def test_should_raise_ign_client_error_when_no_elevation(self) -> None:
        respx.get(_ALTIMETRIE_BASE_URL).mock(return_value=Response(200, json={"elevations": []}))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_altitude(0.0, 0.0)

    @respx.mock
    async def test_should_raise_ign_client_error_when_elevations_key_missing(self) -> None:
        respx.get(_ALTIMETRIE_BASE_URL).mock(return_value=Response(200, json={}))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_altitude(0.0, 0.0)

    @respx.mock
    async def test_should_raise_ign_client_error_when_http_status_failure(self) -> None:
        respx.get(_ALTIMETRIE_BASE_URL).mock(return_value=Response(500))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_altitude(44.0, -0.5)

    @respx.mock
    async def test_should_raise_ign_client_error_when_network_error(self) -> None:
        respx.get(_ALTIMETRIE_BASE_URL).mock(side_effect=httpx.ConnectError("boom"))
        client = IGNClient()

        with pytest.raises(IGNClientError):
            await client.get_altitude(44.0, -0.5)

    @respx.mock
    async def test_should_send_expected_query_params(self) -> None:
        route = respx.get(_ALTIMETRIE_BASE_URL).mock(
            return_value=Response(200, json={"elevations": [1.0]})
        )
        client = IGNClient()

        await client.get_altitude(latitude=44.85, longitude=-0.54)

        request = route.calls.last.request
        assert request.url.params["lat"] == "44.85"
        assert request.url.params["lon"] == "-0.54"
        assert request.url.params["resource"] == "ign_rge_alti_wld"
        assert request.url.params["zonly"] == "true"


# =====================================================================
# Résilience IGNClient — modes de panne supplémentaires (GSIE-PROMPT-0023)
# =====================================================================


class TestGetParcelleResilience:
    """get_parcelle() — modes de panne non couverts par les tests ci-dessus."""

    @respx.mock
    async def test_should_raise_ign_client_error_when_json_invalid(self) -> None:
        """Mode #3 — un corps JSON malformé doit lever IGNClientError, pas planter."""
        respx.get(_CADASTRE_BASE_URL).mock(
            return_value=Response(200, content=b"<<< pas du JSON >>>")
        )
        client = IGNClient()
        with pytest.raises(IGNClientError, match="Échec de l'appel API Carto Cadastre"):
            await client.get_parcelle("33063", "AM", "0001")

    @respx.mock
    async def test_should_return_none_when_features_not_a_list(self) -> None:
        """Mode #4 — une réponse JSON valide mais 'features' absent doit retourner None.

        Le client utilise data.get("features", []) qui retourne [] si la clé
        est absente — le résultat doit être None, jamais une erreur.
        """
        respx.get(_CADASTRE_BASE_URL).mock(
            return_value=Response(200, json={"type": "FeatureCollection"})
        )
        client = IGNClient()
        result = await client.get_parcelle("33063", "AM", "0001")
        assert result is None


class TestGetAltitudeResilience:
    """get_altitude() — modes de panne non couverts par les tests ci-dessus."""

    @respx.mock
    async def test_should_raise_ign_client_error_when_json_invalid(self) -> None:
        """Mode #3 — un corps JSON malformé doit lever IGNClientError, pas planter."""
        respx.get(_ALTIMETRIE_BASE_URL).mock(
            return_value=Response(200, content=b"<<< pas du JSON >>>")
        )
        client = IGNClient()
        with pytest.raises(IGNClientError, match="Échec de l'appel API de calcul altimétrique"):
            await client.get_altitude(44.0, -0.5)

    @respx.mock
    async def test_should_raise_ign_client_error_when_elevation_not_numeric(self) -> None:
        """Mode #4 — une élévation non-numérique doit lever IGNClientError.

        Le client fait float(elevations[0]) — une chaîne non-numérique doit
        lever IGNClientError, pas planter avec un ValueError non wrappé.
        """
        respx.get(_ALTIMETRIE_BASE_URL).mock(
            return_value=Response(200, json={"elevations": ["not a number"]})
        )
        client = IGNClient()
        with pytest.raises(IGNClientError):
            await client.get_altitude(44.0, -0.5)


async def test_ign_mode5_quota_auth_not_applicable() -> None:
    """Mode #5 — N/A : les API IGN Géoplateforme ne requièrent aucune authentification."""
    pass
