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


@respx.mock
async def test_should_raise_arome_client_error_when_401_403_429_on_get_capabilities() -> None:
    """Mode #5 — un 401/403/429 (auth/quota) sur GetCapabilities doit lever AromeClientError.

    AROME nécessite une clé API (header apikey). Un 401/403/429 indique
    un problème d'authentification ou de quota — le client doit lever
    AromeClientError, jamais planter silencieusement.
    """
    client = AromeClient()
    for status in (401, 403, 429):
        respx.get(_GET_CAPABILITIES_URL).mock(return_value=Response(status))
        with pytest.raises(AromeClientError, match="GetCapabilities"):
            await client.get_latest_temperature_2m_run()


class TestLigneCsvIncomplete:
    """Une ligne amont plus courte que l'en-tête ne doit pas faire un 500.

    `csv.DictReader` rend `None` pour les colonnes absentes d'une ligne
    tronquée. Le moteur convertissait ce `None` directement (`int(None)`,
    `float(None)`), donc échouait en `TypeError` — un 500 opaque pour une
    défaillance qui vient du fournisseur. Une mesure manquante est nommée,
    jamais remplacée par une valeur par défaut (ADR-009).
    """

    def test_un_champ_obligatoire_absent_est_nomme(self) -> None:
        from gsie_api.engines.climate.engine import ClimateEngineError, _champ_obligatoire

        with pytest.raises(ClimateEngineError) as erreur:
            _champ_obligatoire({"dep_code": "01", "niveau_j1": None}, "niveau_j1", "test")

        assert "niveau_j1" in str(erreur.value)

    def test_un_champ_obligatoire_present_est_rendu(self) -> None:
        """Témoin : le refus ci-dessus tient au None, pas à la fonction elle-même."""
        from gsie_api.engines.climate.engine import _champ_obligatoire

        assert _champ_obligatoire({"dep_code": "01"}, "dep_code", "test") == "01"

    def test_une_mesure_optionnelle_absente_reste_none(self) -> None:
        """Une mesure absente vaut None — surtout pas 0.0, qui serait une invention."""
        from gsie_api.engines.climate.engine import _parse_float

        assert _parse_float({"t": None}, "t") is None
        assert _parse_float({"t": "  "}, "t") is None
        assert _parse_float({"t": "12.5"}, "t") == 12.5
