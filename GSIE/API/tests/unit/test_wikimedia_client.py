"""Tests unitaires — WikimediaClient (images Commons + descriptions Wikipédia).

Couvre les 5 modes de panne pour le client Wikimedia. Aucune
authentification requise — le mode #5 (quota/auth) est déclaré N/A.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.engines.botanical.wikimedia_client import (
    WikimediaClient,
    WikimediaClientError,
)

_COMMONS_URL = "https://commons.wikimedia.org/w/api.php"
_WIKIPEDIA_URL = "https://en.wikipedia.org/w/api.php"


# --- Réponses valides de référence ---

_VALID_COMMONS_RESPONSE = {
    "query": {
        "pages": [
            {
                "pageid": 12345,
                "ns": 6,
                "title": "File:Abies alba.jpg",
                "imageinfo": [
                    {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Abies_alba.jpg",
                        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Abies_alba.jpg/400px-Abies_alba.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Abies_alba.jpg",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 3.0"},
                            "Artist": {
                                "value": (
                                    '<a href="//commons.wikimedia.org/wiki/User:Test">'
                                    "Test User</a>"
                                )
                            },
                        },
                    }
                ],
            }
        ]
    }
}

_VALID_WIKIPEDIA_RESPONSE = {
    "query": {
        "pages": {
            "12345": {
                "title": "Abies alba",
                "extract": (
                    "Abies alba, the European silver fir, "
                    "is a fir native to the mountains of Europe."
                ),
            }
        }
    }
}


# --- Mode #1 : panne réseau ---


@respx.mock
async def test_should_raise_wikimedia_error_when_connect_error_on_commons() -> None:
    """Mode #1 — une panne réseau sur Commons doit lever WikimediaClientError."""
    respx.get(_COMMONS_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = WikimediaClient()
    with pytest.raises(WikimediaClientError, match="Échec de la recherche Commons"):
        await client.search_species_images("Abies alba")


@respx.mock
async def test_should_raise_wikimedia_error_when_connect_error_on_wikipedia() -> None:
    """Mode #1 — une panne réseau sur Wikipédia doit lever WikimediaClientError."""
    respx.get(_WIKIPEDIA_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
    client = WikimediaClient()
    with pytest.raises(WikimediaClientError, match="Échec de l'extrait Wikipédia"):
        await client.get_species_description("Abies alba")


# --- Mode #2 : HTTP 4xx/5xx ---


@respx.mock
async def test_should_raise_wikimedia_error_when_http_4xx_on_commons() -> None:
    """Mode #2 — un statut HTTP 4xx sur Commons doit lever WikimediaClientError."""
    client = WikimediaClient()
    respx.get(_COMMONS_URL).mock(return_value=Response(403))
    with pytest.raises(WikimediaClientError):
        await client.search_species_images("Abies alba")


@respx.mock
async def test_should_raise_wikimedia_error_when_http_5xx_on_wikipedia() -> None:
    """Mode #2 — un statut HTTP 5xx sur Wikipédia doit lever WikimediaClientError."""
    client = WikimediaClient()
    respx.get(_WIKIPEDIA_URL).mock(return_value=Response(500))
    with pytest.raises(WikimediaClientError):
        await client.get_species_description("Abies alba")


# --- Mode #3 : corps malformé ---


@respx.mock
async def test_should_raise_wikimedia_error_when_json_invalid_on_commons() -> None:
    """Mode #3 — un corps JSON malformé sur Commons doit lever WikimediaClientError."""
    respx.get(_COMMONS_URL).mock(return_value=Response(200, content=b"<<< pas du JSON >>>"))
    client = WikimediaClient()
    with pytest.raises(WikimediaClientError):
        await client.search_species_images("Abies alba")


# --- Mode #4 : champ absent (réponse valide mais vide) ---


@respx.mock
async def test_should_return_empty_list_when_commons_returns_no_pages() -> None:
    """Mode #4 — une réponse Commons sans pages doit retourner une liste vide."""
    respx.get(_COMMONS_URL).mock(return_value=Response(200, json={"query": {"pages": []}}))
    client = WikimediaClient()
    result = await client.search_species_images("NonExistentSpecies")
    assert result == []


@respx.mock
async def test_should_return_none_when_wikipedia_returns_no_extract() -> None:
    """Mode #4 — une réponse Wikipédia sans extrait doit retourner None."""
    respx.get(_WIKIPEDIA_URL).mock(
        return_value=Response(
            200,
            json={"query": {"pages": {"1": {"title": "Test", "extract": ""}}}},
        )
    )
    client = WikimediaClient()
    result = await client.get_species_description("NonExistentSpecies")
    assert result is None


@respx.mock
async def test_should_return_none_when_wikipedia_returns_empty_pages() -> None:
    """Mode #4 — une réponse Wikipédia avec pages vides doit retourner None."""
    respx.get(_WIKIPEDIA_URL).mock(return_value=Response(200, json={"query": {"pages": {}}}))
    client = WikimediaClient()
    result = await client.get_species_description("NonExistentSpecies")
    assert result is None


# --- Tests fonctionnels (réponse valide complète) ---


@respx.mock
async def test_should_parse_image_info_when_commons_returns_valid_response() -> None:
    """Une réponse Commons valide doit être parsée en liste d'images."""
    respx.get(_COMMONS_URL).mock(return_value=Response(200, json=_VALID_COMMONS_RESPONSE))
    client = WikimediaClient()
    images = await client.search_species_images("Abies alba")
    assert len(images) == 1
    img = images[0]
    assert "upload.wikimedia.org" in img["url"]
    assert img["license"] == "CC BY-SA 3.0"
    assert "Test User" in img["photographer"]  # HTML stripped
    assert img["title"] == "File:Abies alba.jpg"


@respx.mock
async def test_should_return_extract_when_wikipedia_returns_valid_response() -> None:
    """Une réponse Wikipédia valide doit retourner l'extrait en plain text."""
    respx.get(_WIKIPEDIA_URL).mock(return_value=Response(200, json=_VALID_WIKIPEDIA_RESPONSE))
    client = WikimediaClient()
    extract = await client.get_species_description("Abies alba")
    assert extract is not None
    assert "European silver fir" in extract


# --- Test User-Agent ---


def test_should_include_user_agent_in_auth_headers() -> None:
    """Le client doit inclure un User-Agent (politique Wikimedia)."""
    client = WikimediaClient()
    headers = client.auth_headers()
    assert "User-Agent" in headers
    assert "GSIE" in headers["User-Agent"]


# ===========================================================================
# Couverture complémentaire — lignes 111, 114, 209
# ===========================================================================


@respx.mock
async def test_should_skip_non_dict_pages() -> None:
    """_parse_images doit skip les pages qui ne sont pas des dict."""
    # Une page non-dict (string) doit être skipée
    response_data = {
        "query": {"pages": ["not a dict", {"imageinfo": [{"url": "https://example.com/img.jpg"}]}]}
    }
    respx.get(_COMMONS_URL).mock(return_value=Response(200, json=response_data))
    client = WikimediaClient()
    images = await client.search_species_images("Abies alba")
    # Seule la page dict avec imageinfo doit être retenue
    assert len(images) == 1
    assert images[0]["url"] == "https://example.com/img.jpg"


@respx.mock
async def test_should_skip_pages_without_imageinfo() -> None:
    """_parse_images doit skip les pages sans imageinfo."""
    response_data = {
        "query": {
            "pages": [
                {"title": "File:NoImage.jpg"},  # pas de imageinfo
                {"imageinfo": [{"url": "https://example.com/img.jpg"}]},
            ]
        }
    }
    respx.get(_COMMONS_URL).mock(return_value=Response(200, json=response_data))
    client = WikimediaClient()
    images = await client.search_species_images("Abies alba")
    assert len(images) == 1


def test_should_return_empty_string_when_html_is_falsy() -> None:
    """_strip_html doit retourner '' quand html est falsy."""
    from gsie_api.engines.botanical.wikimedia_client import _strip_html

    assert _strip_html("") == ""
    assert _strip_html(None) == ""
