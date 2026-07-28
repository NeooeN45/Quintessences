"""Tests unitaires — MeteoFranceClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client Météo des forêts.
Authentification par header apikey — le mode #5 teste 401/403/429.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.climate.meteofrance_client import (
    _BASE_URL,
    MeteoFranceClient,
    MeteoFranceClientError,
)

_CARTE_URL = f"{_BASE_URL}/carte/encours"


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "gsie_api.engines.climate.meteofrance_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


@respx.mock
async def test_should_raise_meteofrance_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever MeteoFranceClientError."""
    respx.get(_CARTE_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = MeteoFranceClient()
    with pytest.raises(MeteoFranceClientError, match="Échec de l'appel"):
        await client.get_danger_feux_departements()


@respx.mock
async def test_should_raise_meteofrance_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever MeteoFranceClientError."""
    client = MeteoFranceClient()
    respx.get(_CARTE_URL).mock(return_value=Response(404))
    with pytest.raises(MeteoFranceClientError):
        await client.get_danger_feux_departements()

    respx.get(_CARTE_URL).mock(return_value=Response(500))
    with pytest.raises(MeteoFranceClientError):
        await client.get_danger_feux_departements()


@respx.mock
async def test_should_return_empty_list_when_csv_body_is_empty() -> None:
    """Mode #3 — un corps CSV vide (pas de données) doit retourner une liste vide.

    Un CSV sans en-tête ni ligne de données produit un DictReader vide.
    Le client ne lève pas — il retourne une liste vide. C'est le
    comportement attendu : pas de donnée amont = pas de résultat, jamais
    de valeur inventée.
    """
    respx.get(_CARTE_URL).mock(return_value=Response(200, text=""))
    client = MeteoFranceClient()
    result = await client.get_danger_feux_departements()
    assert result == []


@respx.mock
async def test_should_return_rows_with_only_partial_columns_when_csv_truncated() -> None:
    """Mode #4 — un CSV tronqué (colonnes manquantes) doit produire des lignes avec None.

    Le corps est bien formé (HTTP 200, content-type CSV) mais les colonnes
    attendues sont absentes. DictReader remplit avec None — aucune valeur
    inventée. Le client ne lève pas car le CSV est syntaxiquement valide.
    """
    # CSV avec en-tête mais sans les colonnes niveau_j1/niveau_j2
    truncated_csv = "reference_time;dep_code;dep_nom\n2026-07-17T14:50:06Z;01;Ain\n"
    respx.get(_CARTE_URL).mock(return_value=Response(200, text=truncated_csv))
    client = MeteoFranceClient()
    result = await client.get_danger_feux_departements()
    assert len(result) == 1
    assert result[0]["dep_code"] == "01"
    assert result[0].get("niveau_j1") is None
    assert result[0].get("niveau_j2") is None


@respx.mock
async def test_should_raise_meteofrance_client_error_when_401_403_429() -> None:
    """Mode #5 — un 401/403/429 (auth/quota) doit lever MeteoFranceClientError."""
    client = MeteoFranceClient()
    for status in (401, 403, 429):
        respx.get(_CARTE_URL).mock(return_value=Response(status))
        with pytest.raises(MeteoFranceClientError, match="Échec"):
            await client.get_danger_feux_departements()
