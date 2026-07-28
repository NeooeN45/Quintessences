"""Tests unitaires — VigilanceClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client Vigilance (Météo-France).
Authentification par header apikey — le mode #5 teste 401/403/429.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.climate.vigilance_client import (
    _URL,
    VigilanceClient,
    VigilanceClientError,
)


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "gsie_api.engines.climate.vigilance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


@respx.mock
async def test_should_raise_vigilance_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever VigilanceClientError."""
    respx.get(_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = VigilanceClient()
    with pytest.raises(VigilanceClientError, match="Échec de l'appel"):
        await client.get_carte_vigilance()


@respx.mock
async def test_should_raise_vigilance_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever VigilanceClientError."""
    client = VigilanceClient()
    respx.get(_URL).mock(return_value=Response(404))
    with pytest.raises(VigilanceClientError):
        await client.get_carte_vigilance()

    respx.get(_URL).mock(return_value=Response(500))
    with pytest.raises(VigilanceClientError):
        await client.get_carte_vigilance()


@respx.mock
async def test_should_raise_vigilance_client_error_when_json_invalid() -> None:
    """Mode #3 — un corps JSON malformé doit lever VigilanceClientError."""
    respx.get(_URL).mock(return_value=Response(200, content=b"<<< pas du JSON >>>"))
    client = VigilanceClient()
    with pytest.raises(VigilanceClientError):
        await client.get_carte_vigilance()


@respx.mock
async def test_should_return_raw_dict_when_product_key_absent() -> None:
    """Mode #4 — une réponse JSON valide mais sans 'product' doit retourner le dict brut.

    Le client VigilanceClient retourne le JSON brut sans validation de
    structure — c'est l'engine qui interprète. Une réponse sans 'product'
    est donc retournée telle quelle, sans erreur. Le test vérifie que le
    client ne plante pas et retourne bien le dict reçu.
    """
    respx.get(_URL).mock(return_value=Response(200, json={"unexpected": "structure"}))
    client = VigilanceClient()
    result = await client.get_carte_vigilance()
    assert result == {"unexpected": "structure"}


@respx.mock
async def test_should_raise_vigilance_client_error_when_401_403_429() -> None:
    """Mode #5 — un 401/403/429 (auth/quota) doit lever VigilanceClientError."""
    client = VigilanceClient()
    for status in (401, 403, 429):
        respx.get(_URL).mock(return_value=Response(status))
        with pytest.raises(VigilanceClientError, match="Échec"):
            await client.get_carte_vigilance()
