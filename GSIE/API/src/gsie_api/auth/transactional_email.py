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

    async def send_organisation_invitation(
        self,
        email: str,
        organisation_name: str,
        invite_url: str,
        role: str,
    ) -> bool: ...

    async def send_email_change_code(
        self,
        email: str,
        code: str,
        is_new_address: bool,
    ) -> bool: ...

    async def send_deletion_cancellation_code(self, email: str, code: str) -> bool: ...


class DisabledTransactionalEmailSender:
    """Expéditeur fermé explicitement, utilisé hors environnement configuré."""

    is_configured = False

    async def send_verification(self, email: str, code: str) -> bool:
        del email, code
        return False

    async def send_password_reset(self, email: str, code: str) -> bool:
        del email, code
        return False

    async def send_organisation_invitation(
        self,
        email: str,
        organisation_name: str,
        invite_url: str,
        role: str,
    ) -> bool:
        del email, organisation_name, invite_url, role
        return False

    async def send_email_change_code(
        self,
        email: str,
        code: str,
        is_new_address: bool,
    ) -> bool:
        del email, code, is_new_address
        return False

    async def send_deletion_cancellation_code(self, email: str, code: str) -> bool:
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

    async def send_organisation_invitation(
        self,
        email: str,
        organisation_name: str,
        invite_url: str,
        role: str,
    ) -> bool:
        return await self._send(
            email=email,
            subject=f"Invitation à rejoindre {organisation_name}",
            body=(
                f"Vous êtes invité à rejoindre l'organisation {organisation_name}.\n\n"
                f"Rôle proposé : {role}.\n\n"
                f"Acceptez l'invitation ici : {invite_url}\n\n"
                f"Le lien expire dans {self._settings.organisation_invitation_expire_hours} heures."
            ),
            purpose="organisation_invitation",
        )

    async def send_email_change_code(
        self,
        email: str,
        code: str,
        is_new_address: bool,
    ) -> bool:
        return await self._send(
            email=email,
            subject="Confirmation de changement d'adresse Quintessences",
            body=(
                "Confirmez votre nouvelle adresse e-mail avec ce code : "
                if is_new_address
                else "Confirmez la demande de changement d'adresse avec ce code : "
            )
            + (
                f"{code}\n\nCe code expire dans "
                f"{self._settings.identity_action_code_expire_minutes} minutes."
            ),
            purpose="email_change",
        )

    async def send_deletion_cancellation_code(self, email: str, code: str) -> bool:
        return await self._send(
            email=email,
            subject="Annulation de la suppression de votre compte Quintessences",
            body=(
                f"Votre code d'annulation de suppression est : {code}\n\n"
                f"Il expire dans {self._settings.identity_action_code_expire_minutes} minutes."
            ),
            purpose="cancel_deletion",
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
