"""Vérificateur OIDC générique — Keycloak, Microsoft Entra ID, GitHub, etc.

Contrairement à Google qui a sa bibliothèque dédiée, ce vérificateur utilise
la découverte OIDC standard (.well-known/openid-configuration) et valide les
ID tokens via les JWKS publiées par le fournisseur.

Configuration via GSIE_OIDC_PROVIDERS : liste JSON de fournisseurs.
Chaque fournisseur : {"name", "issuer", "client_ids", "jwks_url"}.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

import jwt
from jwt import PyJWKClient

from gsie_api.auth.identity import GoogleIdentity, InvalidEmailError, normalize_email
from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = get_logger("gsie_api.auth.oidc_generic")


class InvalidOidcTokenError(ValueError):
    """Le jeton OIDC générique ne satisfait pas le contrat d'identité."""


@dataclass(frozen=True, slots=True)
class OidcProviderConfig:
    """Configuration d'un fournisseur OIDC enterprise."""

    name: str
    issuer: str
    client_ids: tuple[str, ...]
    jwks_url: str


class OidcVerifierProtocol(Protocol):
    """Contrat de vérification d'un jeton OIDC générique."""

    @property
    def is_configured(self) -> bool: ...

    async def verify(self, token: str, provider_name: str) -> GoogleIdentity: ...


class GenericOidcVerifier:
    """Vérifie des ID tokens OIDC pour des fournisseurs configurables.

    Réutilise le type ``GoogleIdentity`` car le contrat d'identité est
    identique : issuer + subject + email + display_name.
    """

    def __init__(self, providers: tuple[OidcProviderConfig, ...]) -> None:
        self._providers = {p.name: p for p in providers if p.name}

    @property
    def is_configured(self) -> bool:
        return bool(self._providers)

    def get_provider_names(self) -> list[str]:
        return list(self._providers.keys())

    async def verify(self, token: str, provider_name: str) -> GoogleIdentity:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise InvalidOidcTokenError(f"Fournisseur OIDC inconnu : {provider_name}")

        claims = await self._verify_token(token, provider)
        return self._identity_from_claims(claims, provider)

    async def _verify_token(self, token: str, provider: OidcProviderConfig) -> Mapping[str, object]:
        """Valide la signature via JWKS et les claims standards OIDC."""

        def verify_sync() -> Mapping[str, object]:
            jwks_client = PyJWKClient(provider.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            for client_id in provider.client_ids:
                try:
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=["RS256"],
                        audience=client_id,
                        issuer=provider.issuer,
                        options={"require": ["sub", "iss", "aud", "iat", "exp"]},
                    )
                    return cast("Mapping[str, object]", payload)
                except jwt.InvalidTokenError:
                    continue
            raise InvalidOidcTokenError("Aucune audience OIDC valide")

        return await asyncio.to_thread(verify_sync)

    def _identity_from_claims(
        self,
        claims: Mapping[str, object],
        provider: OidcProviderConfig,
    ) -> GoogleIdentity:
        subject = claims.get("sub")
        email = claims.get("email")
        email_verified = claims.get("email_verified")

        if not isinstance(subject, str) or not subject or len(subject) > 255:
            raise InvalidOidcTokenError("Sujet OIDC invalide")
        if not isinstance(email, str) or email_verified is not True:
            raise InvalidOidcTokenError("Adresse OIDC non vérifiée")

        display_name_claim: Any = claims.get("name") or claims.get("preferred_username")
        display_name = (
            display_name_claim[:200]
            if isinstance(display_name_claim, str) and display_name_claim.strip()
            else None
        )
        try:
            normalized_email = normalize_email(email)
        except InvalidEmailError:
            raise InvalidOidcTokenError("Adresse OIDC invalide") from None

        return GoogleIdentity(
            issuer=provider.issuer,
            subject=subject,
            email=normalized_email,
            display_name=display_name,
        )


def load_oidc_providers() -> tuple[OidcProviderConfig, ...]:
    """Charge les fournisseurs OIDC depuis la configuration."""
    settings = get_settings()
    providers: list[OidcProviderConfig] = []
    for raw in settings.oidc_providers:
        try:
            name = str(raw.get("name", ""))
            issuer = str(raw.get("issuer", ""))
            jwks_url = str(raw.get("jwks_url", ""))
            if not name or not issuer or not jwks_url:
                continue
            client_ids_raw = raw.get("client_ids", [])
            if not isinstance(client_ids_raw, list):
                continue
            client_ids = tuple(str(c) for c in client_ids_raw if isinstance(c, str) and c)
            if not client_ids:
                continue
            providers.append(
                OidcProviderConfig(
                    name=name,
                    issuer=issuer,
                    client_ids=client_ids,
                    jwks_url=jwks_url,
                )
            )
        except (KeyError, TypeError):
            logger.warning("oidc_provider_config_invalid", raw=raw)
            continue
    return tuple(providers)


_generic_verifier: GenericOidcVerifier | None = None


def get_generic_oidc_verifier() -> GenericOidcVerifier:
    """Construit le vérificateur OIDC générique (singleton de processus)."""
    global _generic_verifier
    if _generic_verifier is None:
        _generic_verifier = GenericOidcVerifier(load_oidc_providers())
    return _generic_verifier
