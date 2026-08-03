"""Validation serveur des jetons Google OpenID Connect (DEC-000044)."""

from __future__ import annotations

import asyncio
import hmac
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token

from gsie_api.auth.identity import GoogleIdentity, InvalidEmailError, normalize_email

GoogleVerifyCallable = Callable[[str, str], Awaitable[Mapping[str, object]]]


class InvalidGoogleTokenError(ValueError):
    """Le jeton Google ne satisfait pas le contrat d'identité."""


async def _verify_with_google_library(token: str, audience: str) -> Mapping[str, object]:
    """Exécute la bibliothèque officielle hors de la boucle asyncio."""

    def verify() -> Mapping[str, object]:
        claims = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
            token,
            GoogleAuthRequest(),
            audience,
        )
        return cast("Mapping[str, object]", claims)

    return await asyncio.to_thread(verify)


class GoogleTokenVerifier:
    """Vérifie un ID token pour l'une des audiences clientes autorisées."""

    _ISSUERS = frozenset({"https://accounts.google.com", "accounts.google.com"})

    def __init__(
        self,
        client_ids: tuple[str, ...],
        verify_token: GoogleVerifyCallable = _verify_with_google_library,
    ) -> None:
        self._client_ids = tuple(client_id for client_id in client_ids if client_id.strip())
        self._verify_token = verify_token

    @property
    def is_configured(self) -> bool:
        return bool(self._client_ids)

    async def verify(self, token: str, expected_nonce: str) -> GoogleIdentity:
        if not self.is_configured:
            raise InvalidGoogleTokenError("Google non configuré")

        claims: Mapping[str, object] | None = None
        for audience in self._client_ids:
            try:
                claims = await self._verify_token(token, audience)
                break
            except ValueError:
                continue
        if claims is None:
            raise InvalidGoogleTokenError("Jeton Google invalide")

        return self._identity_from_claims(claims, expected_nonce)

    def _identity_from_claims(
        self,
        claims: Mapping[str, object],
        expected_nonce: str,
    ) -> GoogleIdentity:
        issuer = claims.get("iss")
        subject = claims.get("sub")
        email = claims.get("email")
        nonce = claims.get("nonce")
        email_verified = claims.get("email_verified")

        if not isinstance(issuer, str) or issuer not in self._ISSUERS:
            raise InvalidGoogleTokenError("Émetteur Google invalide")
        if not isinstance(subject, str) or not subject or len(subject) > 255:
            raise InvalidGoogleTokenError("Sujet Google invalide")
        if not isinstance(email, str) or email_verified is not True:
            raise InvalidGoogleTokenError("Adresse Google non vérifiée")
        if not isinstance(nonce, str) or not hmac.compare_digest(nonce, expected_nonce):
            raise InvalidGoogleTokenError("Nonce Google invalide")

        display_name_claim: Any = claims.get("name")
        display_name = (
            display_name_claim[:200]
            if isinstance(display_name_claim, str) and display_name_claim.strip()
            else None
        )
        try:
            normalized_email = normalize_email(email)
        except InvalidEmailError:
            raise InvalidGoogleTokenError("Adresse Google invalide") from None
        return GoogleIdentity(
            issuer="https://accounts.google.com",
            subject=subject,
            email=normalized_email,
            display_name=display_name,
        )
