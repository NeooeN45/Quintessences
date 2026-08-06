"""Tests unitaires — TurnstileClient.

Couvre : désactivé, token valide, token rejeté, erreur réseau.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response
from pydantic import SecretStr

from gsie_api.core.config import Settings
from gsie_api.shared.turnstile import (
    TURNSTILE_VERIFY_URL,
    TurnstileClient,
    TurnstileVerificationError,
)


def _settings(enabled: bool = True, secret: str = "test-secret") -> Settings:
    return Settings(
        turnstile_enabled=enabled,
        turnstile_secret_key=SecretStr(secret),
        turnstile_site_key="test-site",
    )


async def test_should_return_true_when_turnstile_disabled() -> None:
    """Pas de vérification quand Turnstile est désactivé."""
    client = TurnstileClient(_settings(enabled=False))
    assert await client.verify("any-token") is True


async def test_should_return_true_when_siteverify_succeeds() -> None:
    """Un token valide retourne True."""
    with respx.mock:
        respx.post(TURNSTILE_VERIFY_URL).mock(
            return_value=Response(
                200,
                json={"success": True, "hostname": "quintessences-platform.com"},
            )
        )
        client = TurnstileClient(_settings())
        assert await client.verify("valid-token") is True


async def test_should_return_false_when_siteverify_rejects_token() -> None:
    """Un token rejeté par Cloudflare retourne False."""
    with respx.mock:
        respx.post(TURNSTILE_VERIFY_URL).mock(
            return_value=Response(
                200,
                json={"success": False, "error-codes": ["timeout-or-duplicate"]},
            )
        )
        client = TurnstileClient(_settings())
        assert await client.verify("invalid-token") is False


async def test_should_return_false_when_token_is_empty() -> None:
    """Un token vide retourne False sans appeler Cloudflare."""
    client = TurnstileClient(_settings())
    assert await client.verify("   ") is False


async def test_should_raise_turnstile_error_when_network_fails() -> None:
    """Une panne réseau lève TurnstileVerificationError."""
    with respx.mock:
        respx.post(TURNSTILE_VERIFY_URL).mock(side_effect=httpx.ConnectError("connexion refusée"))
        client = TurnstileClient(_settings())
        with pytest.raises(TurnstileVerificationError, match="Échec de vérification Turnstile"):
            await client.verify("valid-token")


async def test_should_send_remote_ip_when_provided() -> None:
    """Le remote IP est transmis à Cloudflare."""
    request: respx.Request | None = None

    def _capture(req: respx.Request) -> Response:
        nonlocal request
        request = req
        return Response(200, json={"success": True})

    with respx.mock:
        respx.post(TURNSTILE_VERIFY_URL).mock(side_effect=_capture)
        client = TurnstileClient(_settings())
        await client.verify("valid-token", remote_ip="1.2.3.4")

    assert request is not None
    assert b"remoteip=1.2.3.4" in request.content
