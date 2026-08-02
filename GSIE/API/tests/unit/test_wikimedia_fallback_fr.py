"""Tests unitaires — WikimediaClient.get_species_description_with_fallback.

Vérifie le fallback EN → FR introduit par l'audit qualité base du
2026-08-01 (P3-2) et le filtrage des descriptions < 100 chars (P2-1).
"""

from __future__ import annotations

import respx
from httpx import Response

from gsie_api.engines.botanical.wikimedia_client import (
    _MIN_DESCRIPTION_LENGTH,
    WikimediaClient,
)

_WIKIPEDIA_EN_URL = "https://en.wikipedia.org/w/api.php"
_WIKIPEDIA_FR_URL = "https://fr.wikipedia.org/w/api.php"


def _wikipedia_response(extract: str) -> dict[str, object]:
    return {"query": {"pages": {"12345": {"title": "Abies alba", "extract": extract}}}}


_LONG_EN = (
    "Abies alba, the European silver fir, is a fir native to the mountains "
    "of Europe. It is a large evergreen coniferous tree growing to 40-50 m."
)
_LONG_FR = (
    "Abies alba, le sapin pectiné, est un arbre conifère de la famille des "
    "Pinaceae. C'est un grand arbre pouvant atteindre 40 à 50 mètres de haut."
)
_SHORT = "Abies alba."  # < 100 chars


@respx.mock
async def test_should_return_en_when_en_extract_is_long_enough() -> None:
    """Si EN est long, on retourne EN sans appeler FR."""
    respx.get(_WIKIPEDIA_EN_URL).mock(
        return_value=Response(200, json=_wikipedia_response(_LONG_EN))
    )
    client = WikimediaClient()
    desc, lang = await client.get_species_description_with_fallback("Abies alba")
    assert desc == _LONG_EN
    assert lang == "en"


@respx.mock
async def test_should_fallback_to_fr_when_en_is_short() -> None:
    """Si EN est trop court (< 100), on essaie FR."""
    respx.get(_WIKIPEDIA_EN_URL).mock(return_value=Response(200, json=_wikipedia_response(_SHORT)))
    respx.get(_WIKIPEDIA_FR_URL).mock(
        return_value=Response(200, json=_wikipedia_response(_LONG_FR))
    )
    client = WikimediaClient()
    desc, lang = await client.get_species_description_with_fallback("Abies alba")
    assert desc == _LONG_FR
    assert lang == "fr"


@respx.mock
async def test_should_fallback_to_fr_when_en_is_none() -> None:
    """Si EN est None (pas d'article), on essaie FR."""
    respx.get(_WIKIPEDIA_EN_URL).mock(return_value=Response(200, json={"query": {"pages": {}}}))
    respx.get(_WIKIPEDIA_FR_URL).mock(
        return_value=Response(200, json=_wikipedia_response(_LONG_FR))
    )
    client = WikimediaClient()
    desc, lang = await client.get_species_description_with_fallback("Abies alba")
    assert desc == _LONG_FR
    assert lang == "fr"


@respx.mock
async def test_should_return_en_short_when_both_short() -> None:
    """Si EN et FR sont tous deux trop courts, on retourne EN (mieux que rien)."""
    respx.get(_WIKIPEDIA_EN_URL).mock(return_value=Response(200, json=_wikipedia_response(_SHORT)))
    respx.get(_WIKIPEDIA_FR_URL).mock(return_value=Response(200, json=_wikipedia_response(_SHORT)))
    client = WikimediaClient()
    desc, lang = await client.get_species_description_with_fallback("Abies alba")
    assert desc == _SHORT
    assert lang == "en"


@respx.mock
async def test_should_return_none_when_both_none() -> None:
    """Si EN et FR sont tous deux None, on retourne (None, '')."""
    respx.get(_WIKIPEDIA_EN_URL).mock(return_value=Response(200, json={"query": {"pages": {}}}))
    respx.get(_WIKIPEDIA_FR_URL).mock(return_value=Response(200, json={"query": {"pages": {}}}))
    client = WikimediaClient()
    desc, lang = await client.get_species_description_with_fallback("Abies alba")
    assert desc is None
    assert lang == ""


def test_min_description_length_is_100() -> None:
    """La constante _MIN_DESCRIPTION_LENGTH doit être 100 (audit P2-1)."""
    assert _MIN_DESCRIPTION_LENGTH == 100


@respx.mock
async def test_should_call_fr_with_language_param() -> None:
    """get_species_description(language='fr') doit appeler fr.wikipedia.org."""
    route = respx.get(_WIKIPEDIA_FR_URL).mock(
        return_value=Response(200, json=_wikipedia_response(_LONG_FR))
    )
    client = WikimediaClient()
    desc = await client.get_species_description("Abies alba", language="fr")
    assert desc == _LONG_FR
    assert route.called


@respx.mock
async def test_should_call_en_with_language_param() -> None:
    """get_species_description(language='en') doit appeler en.wikipedia.org."""
    route = respx.get(_WIKIPEDIA_EN_URL).mock(
        return_value=Response(200, json=_wikipedia_response(_LONG_EN))
    )
    client = WikimediaClient()
    desc = await client.get_species_description("Abies alba", language="en")
    assert desc == _LONG_EN
    assert route.called
