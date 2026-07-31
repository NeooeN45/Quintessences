"""Tests unitaires — retry avec backoff exponentiel sur ResilientHttpClient.

Le retry a été ajouté dans le cadre de l'audit large (P3-1). Ces tests
vérifient que :

1. Le retry a **lieu** sur erreurs transitoires (ConnectError, 429).
2. Le retry **n'a pas lieu** sur erreurs applicatives (4xx sauf 429).
3. Le backoff est **exponentiel** (0.5s, 1s, 2s).
4. Le nombre de tentatives respecte `max_retries`.

Sans ces tests, supprimer le code de retry ferait passer les tests
existants (qui ne vérifient que l'exception finale, pas le nombre
d'appels).
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from gsie_api.shared import http_client
from gsie_api.shared.http_client import ResilientHttpClient


class _TestClient(ResilientHttpClient):
    """Client minimal pour tester le retry sans dépendance métier."""

    @property
    def exception_class(self) -> type[Exception]:
        return RuntimeError

    @property
    def base_url(self) -> str:
        return "https://api.test.example.com"


_URL = "https://api.test.example.com/data"


@respx.mock
async def test_should_retry_on_connect_error_then_succeed() -> None:
    """Une panne transitoire (ConnectError) puis succès — le client retry et réussit."""
    route = respx.get(_URL).mock(
        side_effect=[
            httpx.ConnectError("panne transitoire"),
            httpx.ConnectError("encore"),
            Response(200, json={"ok": True}),
        ]
    )
    client = _TestClient()

    response = await client._request("GET", "/data")

    assert response.status_code == 200
    assert route.call_count == 3, "le client doit avoir retry 2 fois (3 appels total)"


@respx.mock
async def test_should_retry_on_429_then_succeed() -> None:
    """429 (quota) est transitoire — le client retry jusqu'à succès."""
    route = respx.get(_URL).mock(
        side_effect=[
            Response(429),
            Response(200, json={"ok": True}),
        ]
    )
    client = _TestClient()

    response = await client._request("GET", "/data")

    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
async def test_should_not_retry_on_404() -> None:
    """404 est une erreur applicative — pas de retry, exception immédiate."""
    route = respx.get(_URL).mock(return_value=Response(404))
    client = _TestClient()

    with pytest.raises(RuntimeError, match="Échec"):
        await client._request("GET", "/data")

    assert route.call_count == 1, "le client ne doit pas retry sur 404"


@respx.mock
async def test_should_not_retry_on_403() -> None:
    """403 est une erreur applicative — pas de retry."""
    route = respx.get(_URL).mock(return_value=Response(403))
    client = _TestClient()

    with pytest.raises(RuntimeError, match="Échec"):
        await client._request("GET", "/data")

    assert route.call_count == 1


@respx.mock
async def test_should_exhaust_retries_on_persistent_connect_error() -> None:
    """ConnectError persistante — le client épuise ses retries puis lève l'exception."""
    route = respx.get(_URL).mock(side_effect=httpx.ConnectError("panne permanente"))
    client = _TestClient(max_retries=3)

    with pytest.raises(RuntimeError, match="panne permanente"):
        await client._request("GET", "/data")

    # 1 tentative initiale + 3 retries = 4 appels
    assert route.call_count == 4


@respx.mock
async def test_should_exhaust_retries_on_persistent_429() -> None:
    """429 persistant — le client épuise ses retries puis lève l'exception."""
    route = respx.get(_URL).mock(return_value=Response(429))
    client = _TestClient(max_retries=2)

    with pytest.raises(RuntimeError, match="429"):
        await client._request("GET", "/data")

    # 1 tentative initiale + 2 retries = 3 appels
    assert route.call_count == 3


@respx.mock
async def test_backoff_is_exponential(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le backoff doit être exponentiel : 0.5s, 1s, 2s pour 3 retries.

    On mock `asyncio.sleep` pour capturer les délais sans attendre réellement.
    """
    sleeps: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(http_client.asyncio, "sleep", _fake_sleep)

    respx.get(_URL).mock(side_effect=httpx.ConnectError("panne"))
    client = _TestClient(max_retries=3)

    with pytest.raises(RuntimeError):
        await client._request("GET", "/data")

    assert sleeps == [0.5, 1.0, 2.0], f"backoff attendu [0.5, 1.0, 2.0], reçu {sleeps}"


@respx.mock
async def test_no_sleep_on_non_retryable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aucun sleep sur 404 — l'erreur est applicative, pas transitoire."""
    sleeps: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(http_client.asyncio, "sleep", _fake_sleep)

    respx.get(_URL).mock(return_value=Response(404))
    client = _TestClient()

    with pytest.raises(RuntimeError):
        await client._request("GET", "/data")

    assert sleeps == [], "le client ne doit pas sleep sur une erreur non-retryable"


@respx.mock
async def test_should_retry_on_read_timeout() -> None:
    """ReadTimeout est une erreur transitoire — le client retry."""
    route = respx.get(_URL).mock(
        side_effect=[
            httpx.ReadTimeout("lecture expirée"),
            Response(200, json={"ok": True}),
        ]
    )
    client = _TestClient()

    response = await client._request("GET", "/data")

    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
async def test_should_retry_on_remote_protocol_error() -> None:
    """RemoteProtocolError est une erreur transitoire — le client retry."""
    route = respx.get(_URL).mock(
        side_effect=[
            httpx.RemoteProtocolError("protocole cassé"),
            Response(200, json={"ok": True}),
        ]
    )
    client = _TestClient()

    response = await client._request("GET", "/data")

    assert response.status_code == 200
    assert route.call_count == 2
