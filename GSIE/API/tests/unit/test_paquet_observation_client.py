"""Tests unitaires — PaquetObservationClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client Package Observations (Météo-France).
Authentification par header apikey — le mode #5 teste 401/403/429.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.climate.paquet_observation_client import (
    _URL,
    PaquetObservationClient,
    PaquetObservationClientError,
)


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "gsie_api.engines.climate.paquet_observation_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


@respx.mock
async def test_should_raise_paquet_obs_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever PaquetObservationClientError."""
    respx.get(_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = PaquetObservationClient()
    with pytest.raises(PaquetObservationClientError, match="Échec de l'appel"):
        await client.get_observations_horaires("33")


@respx.mock
async def test_should_raise_paquet_obs_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever PaquetObservationClientError."""
    client = PaquetObservationClient()
    respx.get(_URL).mock(return_value=Response(404))
    with pytest.raises(PaquetObservationClientError):
        await client.get_observations_horaires("33")

    respx.get(_URL).mock(return_value=Response(500))
    with pytest.raises(PaquetObservationClientError):
        await client.get_observations_horaires("33")


@respx.mock
async def test_should_return_empty_list_when_csv_body_is_empty() -> None:
    """Mode #3 — un corps CSV vide doit retourner une liste vide, pas planter."""
    respx.get(_URL).mock(return_value=Response(200, text=""))
    client = PaquetObservationClient()
    result = await client.get_observations_horaires("33")
    assert result == []


@respx.mock
async def test_should_return_rows_with_none_when_columns_missing() -> None:
    """Mode #4 — un CSV avec colonnes manquantes doit produire des None, pas planter."""
    truncated_csv = "lat;lon;geo_id_insee\n44.49;-0.79;33042001\n"
    respx.get(_URL).mock(return_value=Response(200, text=truncated_csv))
    client = PaquetObservationClient()
    result = await client.get_observations_horaires("33")
    assert len(result) == 1
    assert result[0]["geo_id_insee"] == "33042001"
    assert result[0].get("t") is None
    assert result[0].get("td") is None


@respx.mock
async def test_should_raise_paquet_obs_client_error_when_401_403_429() -> None:
    """Mode #5 — un 401/403/429 (auth/quota) doit lever PaquetObservationClientError."""
    client = PaquetObservationClient()
    for status in (401, 403, 429):
        respx.get(_URL).mock(return_value=Response(status))
        with pytest.raises(PaquetObservationClientError, match="Échec"):
            await client.get_observations_horaires("33")
