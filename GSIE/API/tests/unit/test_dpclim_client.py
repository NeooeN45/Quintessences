"""Tests unitaires — DPClimClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client DPClim (Météo-France).
Authentification par header apikey — le mode #5 teste 401/403/429.

Les tests de test_infra_coverage.py couvrent déjà les cas : clé absente,
liste-stations succès/HTTP 500, commande succès/polling/jamais prête/
500/JSON invalide/clé manquante. Ce fichier couvre les modes non
encore testés : panne réseau pure (ConnectError) et 401/403/429.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.climate.dpclim_client import (
    _BASE_URL,
    DPClimClient,
    DPClimClientError,
)

_LISTE_STATIONS_URL = f"{_BASE_URL}/liste-stations/quotidienne"
_COMMANDE_URL = f"{_BASE_URL}/commande-station/quotidienne"
_FICHIER_URL = f"{_BASE_URL}/commande/fichier"


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "gsie_api.engines.climate.dpclim_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


@respx.mock
async def test_should_raise_dpclim_client_error_when_connect_error_list_stations() -> None:
    """Mode #1 — une panne réseau (ConnectError) sur liste-stations doit lever DPClimClientError."""
    respx.get(_LISTE_STATIONS_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = DPClimClient()
    with pytest.raises(DPClimClientError, match="liste-stations"):
        await client.list_stations("33")


@respx.mock
async def test_should_raise_dpclim_client_error_when_connect_error_commande() -> None:
    """Mode #1 — panne réseau sur commande-station doit lever DPClimClientError."""
    respx.get(_COMMANDE_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = DPClimClient(poll_interval_s=0.0)
    with pytest.raises(DPClimClientError, match="commande-station"):
        await client.get_donnees_quotidiennes(
            "33042001", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
        )


@respx.mock
async def test_should_raise_dpclim_client_error_when_http_4xx_then_5xx_list_stations() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx sur liste-stations doit lever DPClimClientError."""
    client = DPClimClient()
    respx.get(_LISTE_STATIONS_URL).mock(return_value=Response(404))
    with pytest.raises(DPClimClientError):
        await client.list_stations("33")

    respx.get(_LISTE_STATIONS_URL).mock(return_value=Response(500))
    with pytest.raises(DPClimClientError):
        await client.list_stations("33")


@respx.mock
async def test_should_raise_dpclim_client_error_when_commande_json_invalid() -> None:
    """Mode #3 — un corps JSON malformé sur commande-station doit lever DPClimClientError."""
    respx.get(_COMMANDE_URL).mock(return_value=Response(200, content=b"<<< pas du JSON >>>"))
    client = DPClimClient(poll_interval_s=0.0)
    with pytest.raises(DPClimClientError, match="illisible"):
        await client.get_donnees_quotidiennes(
            "33042001", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
        )


@respx.mock
async def test_should_raise_dpclim_client_error_when_commande_missing_return_key() -> None:
    """Mode #4 — une réponse JSON valide mais sans 'return' doit lever DPClimClientError."""
    respx.get(_COMMANDE_URL).mock(return_value=Response(200, json={"unexpected": "structure"}))
    client = DPClimClient(poll_interval_s=0.0)
    with pytest.raises(DPClimClientError, match="commande-station"):
        await client.get_donnees_quotidiennes(
            "33042001", "2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"
        )


@respx.mock
async def test_should_raise_dpclim_client_error_when_401_403_429_list_stations() -> None:
    """Mode #5 — un 401/403/429 (auth/quota) sur liste-stations doit lever DPClimClientError."""
    client = DPClimClient()
    for status in (401, 403, 429):
        respx.get(_LISTE_STATIONS_URL).mock(return_value=Response(status))
        with pytest.raises(DPClimClientError, match="liste-stations"):
            await client.list_stations("33")
