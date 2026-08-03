"""Livraison SMTP des codes d'identité, sans journaliser de donnée sensible."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from functools import lru_cache
from typing import Protocol

from gsie_api.core.config import Settings, get_settings
from gsie_api.core.logging import get_logger

logger = get_logger("gsie_api.auth.transactional_email")


class TransactionalEmailSender(Protocol):
    """Contrat de livraison des deux messages de sécurité."""

    @property
    def is_configured(self) -> bool: ...

    async def send_verification(self, email: str, code: str) -> bool: ...

    async def send_password_reset(self, email: str, code: str) -> bool: ...


class DisabledTransactionalEmailSender:
    """Expéditeur fermé explicitement, utilisé hors environnement configuré."""

    is_configured = False

    async def send_verification(self, email: str, code: str) -> bool:
        del email, code
        return False

    async def send_password_reset(self, email: str, code: str) -> bool:
        del email, code
        return False


class SmtpTransactionalEmailSender:
    """Client SMTP minimal exécuté hors de la boucle asynchrone."""

    is_configured = True

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification(self, email: str, code: str) -> bool:
        return await self._send(
            email=email,
            subject="Vérifiez votre compte Quintessences",
            body=(
                "Bienvenue dans l'écosystème Quintessences.\n\n"
                f"Votre code de vérification GeoSylva est : {code}\n\n"
                f"Il expire dans {self._settings.identity_action_code_expire_minutes} minutes. "
                "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
            ),
            purpose="verify_email",
        )

    async def send_password_reset(self, email: str, code: str) -> bool:
        return await self._send(
            email=email,
            subject="Réinitialisation de votre compte Quintessences",
            body=(
                f"Votre code de réinitialisation GeoSylva est : {code}\n\n"
                f"Il expire dans {self._settings.identity_action_code_expire_minutes} minutes. "
                "Si vous n'êtes pas à l'origine de cette demande, ne transmettez pas ce code."
            ),
            purpose="reset_password",
        )

    async def _send(self, email: str, subject: str, body: str, purpose: str) -> bool:
        message = EmailMessage()
        message["From"] = self._settings.email_sender
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)
        try:
            await asyncio.to_thread(self._send_sync, message)
        except (OSError, smtplib.SMTPException):
            logger.exception("identity_email_delivery_failed", purpose=purpose)
            return False
        logger.info("identity_email_delivered", purpose=purpose)
        return True

    def _send_sync(self, message: EmailMessage) -> None:
        smtp_class = smtplib.SMTP_SSL if self._settings.smtp_use_tls else smtplib.SMTP
        with smtp_class(
            self._settings.smtp_host,
            self._settings.smtp_port,
            timeout=10,
        ) as client:
            if self._settings.smtp_starttls:
                client.starttls()
            username = self._settings.smtp_username
            password = self._settings.smtp_password.get_secret_value()
            if username:
                client.login(username, password)
            client.send_message(message)


@lru_cache
def get_transactional_email_sender() -> TransactionalEmailSender:
    """Construit l'expéditeur explicitement configuré pour le processus."""
    settings = get_settings()
    if settings.transactional_email_mode != "smtp":
        return DisabledTransactionalEmailSender()
    return SmtpTransactionalEmailSender(settings)
