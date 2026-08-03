"""Tests unitaires — PlantNetClient (identification par image).

Couvre le happy path, les cas limites et la garde de clé API manquante.
Les 5 modes de panne réseau sont couverts par test_resilience_factory.py.

PlantNet API : https://my.plantnet.org/ — 78 810 espèces.
Endpoint : POST /v2/identify/{project}?api-key=KEY (multipart/form-data).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.botanical.plantnet_client import (
    _IDENTIFY_URL,
    PlantNetClient,
    PlantNetClientError,
)

_FAKE_KEY = "test-plantnet-key-12345"
_FAKE_SETTINGS = type("S", (), {"plantnet_api_key": _FAKE_KEY})()


@pytest.fixture(autouse=True)
def _fake_plantnet_key() -> None:
    """Injecte une clé API PlantNet fake pour tous les tests."""
    with patch(
        "gsie_api.engines.botanical.plantnet_client.get_settings",
        return_value=_FAKE_SETTINGS,
    ):
        yield


# --- Happy path ---


@respx.mock
async def should_return_identification_results_when_api_succeeds() -> None:
    """identify doit retourner les résultats quand l'API répond 200."""
    respx.post(_IDENTIFY_URL).mock(
        return_value=Response(
            200,
            json={
                "query": {
                    "project": "all",
                    "images": ["abc123"],
                    "organs": ["auto"],
                },
                "bestMatch": "Quercus robur L.",
                "results": [
                    {
                        "score": 0.85,
                        "species": {
                            "scientificNameWithoutAuthor": "Quercus robur",
                            "scientificNameAuthorship": "L.",
                            "genus": {
                                "scientificNameWithoutAuthor": "Quercus",
                                "scientificName": "Quercus",
                            },
                            "family": {
                                "scientificNameWithoutAuthor": "Fagaceae",
                                "scientificName": "Fagaceae",
                            },
                            "commonNames": ["Chêne pédonculé", "Pedunculate Oak"],
                            "scientificName": "Quercus robur L.",
                        },
                        "gbif": {"id": "2878688"},
                    },
                    {
                        "score": 0.05,
                        "species": {
                            "scientificNameWithoutAuthor": "Quercus petraea",
                            "scientificNameAuthorship": "Matt.",
                            "genus": {
                                "scientificNameWithoutAuthor": "Quercus",
                                "scientificName": "Quercus",
                            },
                            "family": {
                                "scientificNameWithoutAuthor": "Fagaceae",
                                "scientificName": "Fagaceae",
                            },
                            "commonNames": ["Chêne sessile"],
                            "scientificName": "Quercus petraea Matt.",
                        },
                        "gbif": {"id": "2878688"},
                    },
                ],
            },
        )
    )
    client = PlantNetClient()
    result = await client.identify(b"\x89PNG fake image bytes")

    assert result is not None
    assert result["bestMatch"] == "Quercus robur L."
    assert len(result["results"]) == 2
    assert result["results"][0]["score"] == 0.85
    assert result["results"][0]["species"]["scientificName"] == "Quercus robur L."


@respx.mock
async def should_return_none_when_no_results_in_response() -> None:
    """identify doit retourner None quand la réponse ne contient aucun résultat."""
    respx.post(_IDENTIFY_URL).mock(
        return_value=Response(
            200,
            json={
                "query": {"project": "all", "images": ["abc"], "organs": ["auto"]},
                "bestMatch": "",
                "results": [],
            },
        )
    )
    client = PlantNetClient()
    result = await client.identify(b"\x89PNG fake image bytes")
    assert result is None


# --- Garde clé API manquante ---


async def should_raise_plantnet_client_error_when_api_key_missing() -> None:
    """identify doit lever PlantNetClientError si PLANTNET_API_KEY n'est pas configurée."""
    empty_settings = type("S", (), {"plantnet_api_key": None})()
    with patch(
        "gsie_api.engines.botanical.plantnet_client.get_settings",
        return_value=empty_settings,
    ):
        client = PlantNetClient()
        with pytest.raises(PlantNetClientError, match="PLANTNET_API_KEY non configurée"):
            await client.identify(b"\x89PNG fake image bytes")


# --- Edge cases ---


@respx.mock
async def should_raise_error_when_network_fails() -> None:
    """identify doit lever PlantNetClientError sur erreur réseau."""
    respx.post(_IDENTIFY_URL).mock(side_effect=httpx.ConnectError("network down"))
    client = PlantNetClient()
    with pytest.raises(PlantNetClientError, match="Échec de l'identification PlantNet"):
        await client.identify(b"\x89PNG fake image bytes")


@respx.mock
async def should_raise_error_when_http_500() -> None:
    """identify doit lever PlantNetClientError sur HTTP 500."""
    respx.post(_IDENTIFY_URL).mock(return_value=Response(500))
    client = PlantNetClient()
    with pytest.raises(PlantNetClientError):
        await client.identify(b"\x89PNG fake image bytes")


@respx.mock
async def should_raise_error_when_json_malformed() -> None:
    """identify doit lever PlantNetClientError sur corps JSON malformé."""
    respx.post(_IDENTIFY_URL).mock(return_value=Response(200, content=b"<<< not JSON >>>"))
    client = PlantNetClient()
    with pytest.raises(PlantNetClientError):
        await client.identify(b"\x89PNG fake image bytes")


@respx.mock
async def should_return_none_when_results_field_absent() -> None:
    """identify doit retourner None quand le champ results est absent (mode #4)."""
    respx.post(_IDENTIFY_URL).mock(return_value=Response(200, json={"unexpected": "structure"}))
    client = PlantNetClient()
    result = await client.identify(b"\x89PNG fake image bytes")
    assert result is None
