"""Tests unitaires de la route publique de contact."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from starlette.requests import Request

from gsie_api.core.config import Settings
from gsie_api.public_contact import router as contact_router_module
from gsie_api.public_contact.schemas import ContactCategory, PublicContactRequest


def _request() -> Request:
    """Construit une requête minimale avec une adresse réseau déterministe."""

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/public/contact",
            "headers": [],
            "client": ("127.0.0.1", 43100),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
            "root_path": "",
        }
    )


def _settings(enabled: bool = True) -> Settings:
    """Retourne une configuration minimale compatible avec le contact actif."""

    return Settings(
        transactional_email_mode="smtp",
        smtp_host="127.0.0.1",
        smtp_starttls=False,
        public_contact_enabled=enabled,
        public_contact_recipient="owner@example.com" if enabled else None,
        turnstile_enabled=enabled,
        turnstile_secret_key=SecretStr("test-secret" if enabled else ""),
    )


def _payload(**overrides: object) -> PublicContactRequest:
    values: dict[str, object] = {
        "email": "visitor@example.com",
        "category": ContactCategory.partenariat,
        "message": "Bonjour, je souhaite échanger sur un partenariat.",
        "turnstile_token": "token",
        "website": "",
    }
    values.update(overrides)
    return PublicContactRequest.model_validate(values)


async def _call(request: Request, payload: PublicContactRequest, sender: object) -> object:
    """Appelle la fonction originale sous le décorateur de limitation."""

    endpoint = getattr(contact_router_module.submit_contact, "__wrapped__", None)
    assert endpoint is not None
    return await endpoint(request, payload, sender)


async def test_should_transmit_valid_contact_message(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings()
    sender = SimpleNamespace(is_configured=True, send_contact=AsyncMock(return_value=True))

    class TurnstileValide:
        def __init__(self, received_settings: Settings) -> None:
            assert received_settings is settings

        async def verify(self, token: str, remote_ip: str | None = None) -> bool:
            assert token == "token"
            assert remote_ip == "127.0.0.1"
            return True

    monkeypatch.setattr(contact_router_module, "get_settings", lambda: settings)
    monkeypatch.setattr(contact_router_module, "TurnstileClient", TurnstileValide)

    result = await _call(_request(), _payload(), sender)

    assert result.accepted is True
    sender.send_contact.assert_awaited_once_with(
        sender_email="visitor@example.com",
        category="partenariat",
        message="Bonjour, je souhaite échanger sur un partenariat.",
    )


async def test_should_refuse_contact_when_feature_is_disabled() -> None:
    settings = _settings(enabled=False)
    sender = SimpleNamespace(is_configured=True, send_contact=AsyncMock(return_value=True))
    original_get_settings = contact_router_module.get_settings
    contact_router_module.get_settings = lambda: settings
    try:
        with pytest.raises(HTTPException) as error:
            await _call(_request(), _payload(), sender)
    finally:
        contact_router_module.get_settings = original_get_settings

    assert error.value.status_code == 503
    sender.send_contact.assert_not_awaited()


async def test_should_reject_invalid_turnstile_without_sending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings()
    sender = SimpleNamespace(is_configured=True, send_contact=AsyncMock(return_value=True))

    class TurnstileInvalide:
        def __init__(self, received_settings: Settings) -> None:
            del received_settings

        async def verify(self, token: str, remote_ip: str | None = None) -> bool:
            del token, remote_ip
            return False

    monkeypatch.setattr(contact_router_module, "get_settings", lambda: settings)
    monkeypatch.setattr(contact_router_module, "TurnstileClient", TurnstileInvalide)

    with pytest.raises(HTTPException) as error:
        await _call(_request(), _payload(), sender)

    assert error.value.status_code == 401
    sender.send_contact.assert_not_awaited()


async def test_should_drop_honeypot_message_without_delivery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings()
    sender = SimpleNamespace(is_configured=True, send_contact=AsyncMock(return_value=True))
    turnstile = SimpleNamespace(verify=AsyncMock(side_effect=AssertionError("non appelé")))

    monkeypatch.setattr(contact_router_module, "get_settings", lambda: settings)
    monkeypatch.setattr(contact_router_module, "TurnstileClient", lambda _: turnstile)

    result = await _call(_request(), _payload(website="robot"), sender)

    assert result.accepted is True
    sender.send_contact.assert_not_awaited()
    turnstile.verify.assert_not_awaited()
