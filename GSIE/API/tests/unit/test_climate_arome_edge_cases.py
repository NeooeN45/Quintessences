"""Tests unitaires — cas limites du client AROME (couverture edge cases).

Cible les branches réseau non couvertes par `test_climate_arome.py` :

- panne réseau (pas une erreur HTTP applicative) sur `GetCapabilities` ;
- réponse `GetCapabilities` dont le corps n'est pas du XML valide ;
- panne réseau sur `GetCoverage` (distincte du cas déjà couvert
  d'un statut HTTP en échec, `httpx.HTTPStatusError`).

Le réseau est mocké via `respx`, cohérent avec les autres clients HTTP
du dépôt (`IGNClient`, `GBIFClient`) — aucun appel réseau réel.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.climate.arome_client import AromeClient, AromeClientError

_BASE_URL = (
    "https://public-api.meteofrance.fr/public/arome/1.0/wcs/MF-NWP-HIGHRES-AROME-001-FRANCE-WCS"
)
_GET_CAPABILITIES_URL = f"{_BASE_URL}/GetCapabilities"
_GET_COVERAGE_URL = f"{_BASE_URL}/GetCoverage"
_COVERAGE_ID = "TEMPERATURE__SPECIFIC_HEIGHT_LEVEL_ABOVE_GROUND___2026-07-18T06.00.00Z"


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simule une clé METEOFRANCE_API_KEY configurée pour tous les tests de ce module."""
    monkeypatch.setattr(
        "gsie_api.engines.climate.arome_client.get_settings",
        lambda: type("S", (), {"meteofrance_api_key": "fake-key-for-test"})(),
    )


@respx.mock
async def test_should_raise_arome_client_error_when_get_capabilities_network_fails() -> None:
    """Une panne réseau sur GetCapabilities doit lever AromeClientError.

    Distincte d'une erreur HTTP applicative.
    """
    respx.get(_GET_CAPABILITIES_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = AromeClient()

    with pytest.raises(AromeClientError, match="GetCapabilities"):
        await client.get_latest_temperature_2m_run()


@respx.mock
async def test_should_raise_arome_client_error_when_get_capabilities_body_is_not_valid_xml() -> (
    None
):
    """Un corps de réponse GetCapabilities illisible (pas du XML) doit lever AromeClientError."""
    respx.get(_GET_CAPABILITIES_URL).mock(
        return_value=Response(200, content=b"<<< pas du XML valide >>>")
    )
    client = AromeClient()

    with pytest.raises(AromeClientError, match="illisible"):
        await client.get_latest_temperature_2m_run()


@respx.mock
async def test_should_raise_arome_client_error_when_get_coverage_network_fails() -> None:
    """Une panne réseau (pas un statut HTTP en échec) sur GetCoverage doit lever AromeClientError.

    Distinct du cas déjà couvert dans `test_climate_arome.py` d'un
    statut HTTP en échec (`httpx.HTTPStatusError`, ex. 404) — ici la
    requête n'aboutit même pas au serveur.
    """
    respx.get(_GET_COVERAGE_URL).mock(side_effect=httpx.ConnectTimeout("timeout réseau"))
    client = AromeClient()

    with pytest.raises(AromeClientError, match="réseau"):
        await client.get_temperature_2m_grib(
            _COVERAGE_ID,
            latitude=44.8,
            longitude=-0.6,
            echeance=datetime(2026, 7, 18, 12, 0, 0, tzinfo=UTC),
        )
