"""Tests unitaires — SoilGridsClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client SoilGrids (ISRIC).
Aucune authentification requise — le mode #5 (quota/auth) est
déclaré N/A pour ce client.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.pedology.soilgrids_client import (
    _SOILGRIDS_URL,
    SoilGridsClient,
    SoilGridsClientError,
)


@respx.mock
async def test_should_raise_soilgrids_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever SoilGridsClientError."""
    respx.get(_SOILGRIDS_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = SoilGridsClient()
    with pytest.raises(SoilGridsClientError, match="Échec de l'appel SoilGrids"):
        await client.get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_raise_soilgrids_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever SoilGridsClientError."""
    client = SoilGridsClient()
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(404))
    with pytest.raises(SoilGridsClientError):
        await client.get_properties(44.8, -0.6, ["phh2o"])

    respx.get(_SOILGRIDS_URL).mock(return_value=Response(500))
    with pytest.raises(SoilGridsClientError):
        await client.get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_raise_soilgrids_client_error_when_json_invalid() -> None:
    """Mode #3 — un corps JSON malformé doit lever SoilGridsClientError."""
    respx.get(_SOILGRIDS_URL).mock(return_value=Response(200, content=b"<<< pas du JSON >>>"))
    client = SoilGridsClient()
    with pytest.raises(SoilGridsClientError):
        await client.get_properties(44.8, -0.6, ["phh2o"])


@respx.mock
async def test_should_return_empty_dict_when_layers_absent_in_valid_json() -> None:
    """Mode #4 — une réponse JSON valide mais sans 'layers' doit retourner un dict vide.

    Le cas le plus dangereux : une réponse bien formée sans les données
    attendues. La garde utilise data.get("properties", {}).get("layers", [])
    qui retourne [] silencieusement — le résultat doit être un dict vide,
    jamais une valeur inventée.
    """
    respx.get(_SOILGRIDS_URL).mock(
        return_value=Response(200, json={"properties": {}, "status": "ok"})
    )
    client = SoilGridsClient()
    result = await client.get_properties(44.8, -0.6, ["phh2o"])
    assert result == {}


async def test_mode5_quota_auth_not_applicable_for_soilgrids() -> None:
    """Mode #5 — N/A : l'API SoilGrids ne requiert aucune authentification."""
    pass
