"""Tests unitaires — envoi transactionnel (SmtpTransactionalEmailSender)."""

from __future__ import annotations

import smtplib
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

if TYPE_CHECKING:
    from email.message import EmailMessage

from gsie_api.auth.transactional_email import (
    DisabledTransactionalEmailSender,
    SmtpTransactionalEmailSender,
    get_transactional_email_sender,
)
from gsie_api.core.config import Settings


@pytest.fixture
def smtp_settings() -> Settings:
    return Settings(
        transactional_email_mode="smtp",
        smtp_host="127.0.0.1",
        smtp_port=1025,
        smtp_username="",
        smtp_password=SecretStr(""),
        smtp_use_tls=False,
        smtp_starttls=False,
        email_sender="noreply@quintessences-platform.com",
        identity_action_code_expire_minutes=15,
        organisation_invitation_expire_hours=72,
    )


@patch.object(smtplib, "SMTP")
async def test_should_send_verification_email(
    mock_smtp: MagicMock,
    smtp_settings: Settings,
) -> None:
    """Un code de vérification doit être envoyé via SMTP."""
    sender = SmtpTransactionalEmailSender(smtp_settings)
    result = await sender.send_verification("user@example.com", "1234-ABCD")

    assert result is True
    assert mock_smtp.called
    client = mock_smtp.return_value.__enter__.return_value
    assert client.send_message.called
    message: EmailMessage = client.send_message.call_args[0][0]
    assert message["To"] == "user@example.com"
    assert "1234-ABCD" in message.get_content()


@patch.object(smtplib, "SMTP")
async def test_should_return_false_when_smtp_fails(
    mock_smtp: MagicMock,
    smtp_settings: Settings,
) -> None:
    """Une panne SMTP doit être capturée et retourner False."""
    mock_smtp.side_effect = OSError("connexion refusée")
    sender = SmtpTransactionalEmailSender(smtp_settings)
    result = await sender.send_verification("user@example.com", "1234-ABCD")
    assert result is False


def test_should_return_disabled_sender_when_mode_disabled() -> None:
    """Mode 'disabled' retourne l'expéditeur inerte."""
    get_transactional_email_sender.cache_clear()
    with patch("gsie_api.auth.transactional_email.get_settings") as mock_settings:
        mock_settings.return_value = Settings(transactional_email_mode="disabled")
        sender = get_transactional_email_sender()
        assert isinstance(sender, DisabledTransactionalEmailSender)


async def test_should_return_false_when_disabled_sender_used() -> None:
    """L'expéditeur désactivé refuse silencieusement tout envoi."""
    sender = DisabledTransactionalEmailSender()
    assert await sender.send_verification("user@example.com", "1234") is False
    assert await sender.send_password_reset("user@example.com", "5678") is False
