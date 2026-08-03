"""Tests unitaires — vérification des URLs d'images.

Le point tenu par ces tests : **une panne réseau ne doit jamais être lue
comme un lien mort**. La première version du script supprimait
physiquement toute image dont la sonde échouait, quelle que soit la
cause — une micro-coupure pendant une passe `--fix` vidait le catalogue.

Trois verdicts, donc : accessible, disparu, indéterminé. Seul un refus
définitif du serveur (404, 410, 451) déclasse une image, et rien n'est
jamais supprimé (CON-010).
"""

from unittest.mock import patch

import httpx
import pytest
import respx
from validate_image_urls import Verdict, verifier_url

_URL = "https://commons.wikimedia.org/image.jpg"


@pytest.fixture(autouse=True)
def _sans_pause():
    """Neutralise l'attente entre tentatives — les tests ne dorment pas."""
    with patch("validate_image_urls._PAUSE_ENTRE_TENTATIVES", 0):
        yield


async def _verdict(url: str = _URL) -> Verdict:
    async with httpx.AsyncClient() as client:
        return await verifier_url(client, url)


@respx.mock
async def should_declare_accessible_on_2xx():
    respx.head(_URL).mock(return_value=httpx.Response(200))
    assert await _verdict() is Verdict.ACCESSIBLE


@respx.mock
async def should_declare_disparu_on_404():
    respx.head(_URL).mock(return_value=httpx.Response(404))
    assert await _verdict() is Verdict.DISPARU


@respx.mock
async def should_declare_disparu_on_410():
    respx.head(_URL).mock(return_value=httpx.Response(410))
    assert await _verdict() is Verdict.DISPARU


@respx.mock
async def should_not_declare_disparu_on_403():
    """403 ne prouve rien : beaucoup de CDN le renvoient a un client non navigateur."""
    respx.head(_URL).mock(return_value=httpx.Response(403))
    assert await _verdict() is Verdict.INDETERMINE


@respx.mock
async def should_stay_indetermine_when_network_fails():
    """Le cas qui vidait le catalogue : la sonde echoue, le lien reste intact."""
    route = respx.head(_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    assert await _verdict() is Verdict.INDETERMINE
    # Et la sonde a bien reessaye avant de renoncer.
    assert route.call_count == 3


@respx.mock
async def should_stay_indetermine_on_server_error():
    """Un 5xx dit que le serveur va mal, pas que l'image a disparu."""
    respx.head(_URL).mock(return_value=httpx.Response(503))
    assert await _verdict() is Verdict.INDETERMINE


@respx.mock
async def should_retry_until_a_conclusive_verdict():
    """Une panne passagere ne doit pas condamner un lien vivant."""
    route = respx.head(_URL).mock(
        side_effect=[httpx.ConnectTimeout("coupure"), httpx.Response(200)]
    )
    assert await _verdict() is Verdict.ACCESSIBLE
    assert route.call_count == 2


@respx.mock
async def should_fall_back_to_get_when_head_is_refused():
    """405 signifie « pas de HEAD ici », pas « pas d'image »."""
    respx.head(_URL).mock(return_value=httpx.Response(405))
    respx.get(_URL).mock(return_value=httpx.Response(200))
    assert await _verdict() is Verdict.ACCESSIBLE


@respx.mock
async def should_refuse_non_http_schemes_without_calling_out():
    """Une URL `file://` ne doit declencher aucune requete."""
    verdict = await _verdict("file:///etc/passwd")

    assert verdict is Verdict.INDETERMINE
    assert not respx.calls
