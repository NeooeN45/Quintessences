"""Tests unitaires — GBIFClient (résilience aux pannes amont).

Couvre les 5 modes de panne pour le client GBIF (Species Match +
Vernacular Names). Aucune authentification requise — le mode #5
(quota/auth) est déclaré N/A pour ce client.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.botanical.gbif_client import (
    _SPECIES_MATCH_URL,
    GBIFClient,
    GBIFClientError,
)


@respx.mock
async def test_should_raise_gbif_client_error_when_connect_error() -> None:
    """Mode #1 — une panne réseau (ConnectError) doit lever GBIFClientError."""
    respx.get(_SPECIES_MATCH_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = GBIFClient()
    with pytest.raises(GBIFClientError, match="Échec de l'appel GBIF Species Match"):
        await client.match_species("Quercus petraea")


@respx.mock
async def test_should_raise_gbif_client_error_when_http_4xx_then_5xx() -> None:
    """Mode #2 — un statut HTTP 4xx puis 5xx doit lever GBIFClientError."""
    client = GBIFClient()
    # 429 (quota dépassé)
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(429))
    with pytest.raises(GBIFClientError):
        await client.match_species("Quercus petraea")

    # 500 (erreur serveur)
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(500))
    with pytest.raises(GBIFClientError):
        await client.match_species("Quercus petraea")


@respx.mock
async def test_should_raise_gbif_client_error_when_json_invalid() -> None:
    """Mode #3 — un corps JSON malformé doit lever GBIFClientError, pas planter."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(200, content=b"<<< pas du JSON >>>"))
    client = GBIFClient()
    with pytest.raises(GBIFClientError):
        await client.match_species("Quercus petraea")


@respx.mock
async def test_should_return_none_when_usage_key_absent_in_valid_json() -> None:
    """Mode #4 — une réponse JSON valide mais sans usageKey doit retourner None.

    C'est le cas le plus dangereux : une réponse bien formée qui pourrait
    produire silencieusement un None non documenté. La garde vérifie
    matchType == "NONE" OU absence de usageKey.
    """
    respx.get(_SPECIES_MATCH_URL).mock(
        return_value=Response(
            200,
            json={"matchType": "EXACT", "confidence": 99, "kingdom": "Plantae"},
        )
    )
    client = GBIFClient()
    result = await client.match_species("Quercus petraea")
    assert result is None


async def test_mode5_quota_auth_not_applicable_for_gbif() -> None:
    """Mode #5 — N/A : l'API GBIF ne requiert aucune authentification en lecture.

    Déclaré explicitement comme hors d'atteinte avec motif : pas de clé,
    pas de quota, pas de 401/403/429 spécifique à l'auth.
    """
    # Aucun test à exécuter — ce client n'a pas d'authentification.
    # Le mode #2 couvre le 429 si GBIF le renvoie pour surcharge globale.
    pass


# ===========================================================================
# Couverture complémentaire — match_species success + get_vernacular_name
# ===========================================================================


@respx.mock
async def should_return_data_when_match_species_succeeds() -> None:
    """match_species doit retourner les données quand la réponse est valide."""
    respx.get(_SPECIES_MATCH_URL).mock(
        return_value=Response(
            200,
            json={
                "matchType": "EXACT",
                "usageKey": 2878688,
                "scientificName": "Quercus petraea Mert. & W.D.J.Koch",
                "kingdom": "Plantae",
            },
        )
    )
    client = GBIFClient()
    result = await client.match_species("Quercus petraea")
    assert result is not None
    assert result["usageKey"] == 2878688


@respx.mock
async def should_return_none_when_match_type_is_none() -> None:
    """match_species doit retourner None quand matchType == 'NONE'."""
    respx.get(_SPECIES_MATCH_URL).mock(return_value=Response(200, json={"matchType": "NONE"}))
    client = GBIFClient()
    result = await client.match_species("Nonexistent species")
    assert result is None


@respx.mock
async def should_return_vernacular_name_when_results_exist() -> None:
    """get_vernacular_name doit retourner le premier nom vernaculaire."""
    from gsie_api.engines.botanical.gbif_client import _VERNACULAR_NAMES_URL_TEMPLATE

    url = _VERNACULAR_NAMES_URL_TEMPLATE.format(key=2878688)
    respx.get(url).mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {"vernacularName": "Chêne sessile", "language": "fra"},
                    {"vernacularName": "Sessile Oak", "language": "eng"},
                ]
            },
        )
    )
    client = GBIFClient()
    result = await client.get_vernacular_name(2878688, language="fra")
    assert result == "Chêne sessile"


@respx.mock
async def should_return_none_when_no_vernacular_names() -> None:
    """get_vernacular_name doit retourner None quand aucun résultat."""
    from gsie_api.engines.botanical.gbif_client import _VERNACULAR_NAMES_URL_TEMPLATE

    url = _VERNACULAR_NAMES_URL_TEMPLATE.format(key=999999)
    respx.get(url).mock(return_value=Response(200, json={}))
    client = GBIFClient()
    result = await client.get_vernacular_name(999999)
    assert result is None


@respx.mock
async def should_return_none_when_vernacular_results_empty() -> None:
    """get_vernacular_name doit retourner None quand results est une liste vide."""
    from gsie_api.engines.botanical.gbif_client import _VERNACULAR_NAMES_URL_TEMPLATE

    url = _VERNACULAR_NAMES_URL_TEMPLATE.format(key=123)
    respx.get(url).mock(return_value=Response(200, json={"results": []}))
    client = GBIFClient()
    result = await client.get_vernacular_name(123)
    assert result is None


@respx.mock
async def should_raise_error_when_vernacular_name_http_fails() -> None:
    """get_vernacular_name doit lever GBIFClientError sur HTTP 500."""
    from gsie_api.engines.botanical.gbif_client import _VERNACULAR_NAMES_URL_TEMPLATE

    url = _VERNACULAR_NAMES_URL_TEMPLATE.format(key=2878688)
    respx.get(url).mock(return_value=Response(500))
    client = GBIFClient()
    with pytest.raises(GBIFClientError):
        await client.get_vernacular_name(2878688)


@respx.mock
async def should_raise_error_when_vernacular_name_network_fails() -> None:
    """get_vernacular_name doit lever GBIFClientError sur erreur réseau."""
    from gsie_api.engines.botanical.gbif_client import _VERNACULAR_NAMES_URL_TEMPLATE

    url = _VERNACULAR_NAMES_URL_TEMPLATE.format(key=2878688)
    respx.get(url).mock(side_effect=httpx.ConnectError("network down"))
    client = GBIFClient()
    with pytest.raises(GBIFClientError):
        await client.get_vernacular_name(2878688)
