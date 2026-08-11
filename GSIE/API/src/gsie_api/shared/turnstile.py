"""Vérification des tokens Cloudflare Turnstile.

Endpoint documenté :
https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
"""

from __future__ import annotations

from typing import Any, cast

import httpx

from gsie_api.core.config import Settings, get_settings
from gsie_api.core.logging import get_logger

logger = get_logger("gsie_api.shared.turnstile")

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileVerificationError(Exception):
    """Erreur métier de vérification Turnstile."""


class TurnstileClient:
    """Client minimal de vérification des tokens Turnstile."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _is_configured(self) -> bool:
        return self.settings.turnstile_enabled and bool(
            self.settings.turnstile_secret_key.get_secret_value().strip()
        )

    def _build_payload(self, token: str, remote_ip: str | None) -> dict[str, str]:
        data = {
            "secret": self.settings.turnstile_secret_key.get_secret_value(),
            "response": token,
        }
        if remote_ip:
            data["remoteip"] = remote_ip
        return data

    async def _call_siteverify(self, data: dict[str, str]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(TURNSTILE_VERIFY_URL, data=data)
                response.raise_for_status()
                return cast("dict[str, Any]", response.json())
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("turnstile_verification_failed", error=str(exc))
            raise TurnstileVerificationError(f"Échec de vérification Turnstile : {exc}") from exc

    def _is_success(self, payload: dict[str, Any]) -> bool:
        success = payload.get("success") is True
        if not success:
            logger.warning(
                "turnstile_token_rejected",
                error_codes=payload.get("error-codes", []),
            )
            return False
        logger.info("turnstile_token_valid", hostname=payload.get("hostname"))
        return True

    async def verify(self, token: str, remote_ip: str | None = None) -> bool:
        """Vérifie un token Turnstile auprès de Cloudflare.

        Si Turnstile est désactivé, retourne ``True`` (pas de blocage).
        """
        if not self._is_configured():
            return True
        if not token.strip():
            logger.warning("turnstile_token_empty")
            return False

        data = self._build_payload(token, remote_ip)
        payload = await self._call_siteverify(data)
        return self._is_success(payload)

    def get_site_key(self) -> str:
        """Retourne la site key publique pour le widget front-end."""
        return self.settings.turnstile_site_key
