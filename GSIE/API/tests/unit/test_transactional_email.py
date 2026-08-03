"""Livraison transactionnelle des codes d'identité sans fuite de secret."""

from __future__ import annotations

from email.message import EmailMessage
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gsie_api.auth.transactional_email import (
    DisabledTransactionalEmailSender,
    SmtpTransactionalEmailSender,
    get_transactional_email_sender,
)
from gsie_api.core.config import Settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "development",
        "transactional_email_mode": "smtp",
        "smtp_host": "smtp.example.fr",
        "smtp_port": 587,
        "smtp_starttls": True,
        "smtp_use_tls": False,
        "smtp_username": "quintessences",
        "smtp_password": "secret-test",
        "email_sender": "noreply@example.fr",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


async def should_keep_disabled_sender_explicitly_closed() -> None:
    sender = DisabledTransactionalEmailSender()
    assert sender.is_configured is False
    assert await sender.send_verification("a@example.fr", "ABCD-EFGH") is False
    assert await sender.send_password_reset("a@example.fr", "ABCD-EFGH") is False


async def should_build_and_deliver_both_transactional_messages() -> None:
    sender = SmtpTransactionalEmailSender(_settings())
    with patch(
        "gsie_api.auth.transactional_email.asyncio.to_thread",
        new_callable=AsyncMock,
    ) as to_thread:
        assert await sender.send_verification("a@example.fr", "ABCD-EFGH") is True
        assert await sender.send_password_reset("a@example.fr", "WXYZ-2345") is True
    assert to_thread.await_count == 2


async def should_report_smtp_transport_failure_without_raising() -> None:
    sender = SmtpTransactionalEmailSender(_settings())
    with patch(
        "gsie_api.auth.transactional_email.asyncio.to_thread",
        new_callable=AsyncMock,
        side_effect=OSError("relais indisponible"),
    ):
        assert await sender.send_verification("a@example.fr", "ABCD-EFGH") is False


@pytest.mark.parametrize("direct_tls", [False, True])
def should_cover_plain_starttls_and_direct_tls_smtp_clients(direct_tls: bool) -> None:
    settings = _settings(
        smtp_use_tls=direct_tls,
        smtp_starttls=not direct_tls,
        smtp_username="" if direct_tls else "quintessences",
    )
    sender = SmtpTransactionalEmailSender(settings)
    message = EmailMessage()
    message["From"] = "noreply@example.fr"
    message["To"] = "a@example.fr"
    message["Subject"] = "Test"
    message.set_content("Corps")
    client = MagicMock()
    smtp_class = MagicMock()
    smtp_class.return_value.__enter__.return_value = client
    target = "smtplib.SMTP_SSL" if direct_tls else "smtplib.SMTP"

    with patch(f"gsie_api.auth.transactional_email.{target}", smtp_class):
        sender._send_sync(message)  # noqa: SLF001 - transport testé directement

    if direct_tls:
        client.starttls.assert_not_called()
        client.login.assert_not_called()
    else:
        client.starttls.assert_called_once()
        client.login.assert_called_once_with("quintessences", "secret-test")
    client.send_message.assert_called_once_with(message)


def should_build_disabled_or_smtp_sender_from_configuration() -> None:
    get_transactional_email_sender.cache_clear()
    with patch(
        "gsie_api.auth.transactional_email.get_settings",
        return_value=SimpleNamespace(transactional_email_mode="disabled"),
    ):
        assert isinstance(get_transactional_email_sender(), DisabledTransactionalEmailSender)

    get_transactional_email_sender.cache_clear()
    settings = _settings()
    with patch("gsie_api.auth.transactional_email.get_settings", return_value=settings):
        assert isinstance(get_transactional_email_sender(), SmtpTransactionalEmailSender)
    get_transactional_email_sender.cache_clear()
