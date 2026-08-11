"""Couverture du vérificateur OIDC générique (Keycloak, Entra ID, etc.)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from gsie_api.auth import oidc_generic
from gsie_api.auth.identity import InvalidEmailError
from gsie_api.auth.oidc_generic import (
    GenericOidcVerifier,
    InvalidOidcTokenError,
    OidcProviderConfig,
    get_generic_oidc_verifier,
    load_oidc_providers,
)

_PROVIDER = OidcProviderConfig(
    name="keycloak",
    issuer="https://auth.example.test/realms/quintessences",
    client_ids=("geosylva-android",),
    jwks_url="https://auth.example.test/certs",
    authorization_url="https://auth.example.test/authorize",
    allowed_redirect_uris=("com.quintessences.geosylva:/oauth2redirect",),
)

_REDIRECT = "com.quintessences.geosylva:/oauth2redirect"


def should_report_not_configured_without_providers() -> None:
    verifier = GenericOidcVerifier(())
    assert verifier.is_configured is False
    assert verifier.get_provider_names() == []


def should_report_configured_with_providers() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    assert verifier.is_configured is True
    assert verifier.get_provider_names() == ["keycloak"]


def should_reject_authorization_url_for_unknown_provider() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="sans endpoint authorization"):
        verifier.build_authorization_url("inconnu", _REDIRECT, "s" * 16, "c" * 43, "n" * 16)


def should_reject_authorization_url_without_authorization_endpoint() -> None:
    provider = OidcProviderConfig(
        name="no-authz",
        issuer="https://auth.example.test",
        client_ids=("client",),
        jwks_url="https://auth.example.test/certs",
        authorization_url=None,
        allowed_redirect_uris=(_REDIRECT,),
    )
    verifier = GenericOidcVerifier((provider,))
    with pytest.raises(InvalidOidcTokenError, match="sans endpoint authorization"):
        verifier.build_authorization_url("no-authz", _REDIRECT, "s" * 16, "c" * 43, "n" * 16)


def should_reject_authorization_url_for_disallowed_redirect() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="redirect_uri OIDC non autorisée"):
        verifier.build_authorization_url(
            "keycloak", "https://evil.example/callback", "s" * 16, "c" * 43, "n" * 16
        )


@pytest.mark.parametrize(
    "state,code_challenge",
    [("short", "c" * 43), ("s" * 16, "short")],
)
def should_reject_authorization_url_for_weak_pkce(state: str, code_challenge: str) -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="PKCE insuffisants"):
        verifier.build_authorization_url("keycloak", _REDIRECT, state, code_challenge, "n" * 16)


def should_reject_authorization_url_for_weak_nonce() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="Nonce OIDC insuffisant"):
        verifier.build_authorization_url("keycloak", _REDIRECT, "s" * 16, "c" * 43, "short")


def should_reject_authorization_url_for_disallowed_client_id() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="client_id OIDC non autorisé"):
        verifier.build_authorization_url(
            "keycloak", _REDIRECT, "s" * 16, "c" * 43, "n" * 16, client_id="autre-client"
        )


def should_require_explicit_client_id_when_multiple_registered() -> None:
    provider = OidcProviderConfig(
        name="multi",
        issuer="https://auth.example.test",
        client_ids=("client-a", "client-b"),
        jwks_url="https://auth.example.test/certs",
        authorization_url="https://auth.example.test/authorize",
        allowed_redirect_uris=(_REDIRECT,),
    )
    verifier = GenericOidcVerifier((provider,))
    with pytest.raises(InvalidOidcTokenError, match="client_id OIDC non autorisé"):
        verifier.build_authorization_url("multi", _REDIRECT, "s" * 16, "c" * 43, "n" * 16)

    url = verifier.build_authorization_url(
        "multi", _REDIRECT, "s" * 16, "c" * 43, "n" * 16, client_id="client-b"
    )
    assert "client_id=client-b" in url


async def should_raise_for_unknown_provider_on_verify() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="Fournisseur OIDC inconnu"):
        await verifier.verify("token", "inconnu", "nonce-value")


def _claims(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "sub": "user-123",
        "email": "user@example.com",
        "email_verified": True,
        "nonce": "expected-nonce",
        "name": "Jane Doe",
    }
    base.update(overrides)
    return base


async def should_verify_token_trying_multiple_audiences() -> None:
    provider = OidcProviderConfig(
        name="multi",
        issuer="https://auth.example.test",
        client_ids=("client-a", "client-b"),
        jwks_url="https://auth.example.test/certs",
    )
    verifier = GenericOidcVerifier((provider,))
    import jwt as jwt_module

    signing_key = SimpleNamespace(key="the-key")
    jwks_client = MagicMock()
    jwks_client.get_signing_key_from_jwt.return_value = signing_key

    def fake_decode(token: str, key: object, **kwargs: object) -> dict[str, object]:
        if kwargs.get("audience") == "client-a":
            raise jwt_module.InvalidTokenError("mauvaise audience")
        return _claims()

    with (
        patch("gsie_api.auth.oidc_generic.PyJWKClient", return_value=jwks_client),
        patch("gsie_api.auth.oidc_generic.jwt.decode", side_effect=fake_decode),
    ):
        identity = await verifier.verify("token", "multi", "expected-nonce")

    assert identity.subject == "user-123"
    assert identity.email == "user@example.com"
    assert identity.display_name == "Jane Doe"


async def should_raise_when_no_valid_audience_found() -> None:
    provider = OidcProviderConfig(
        name="multi",
        issuer="https://auth.example.test",
        client_ids=("client-a", "client-b"),
        jwks_url="https://auth.example.test/certs",
    )
    verifier = GenericOidcVerifier((provider,))
    import jwt as jwt_module

    jwks_client = MagicMock()
    jwks_client.get_signing_key_from_jwt.return_value = SimpleNamespace(key="the-key")

    with (
        patch("gsie_api.auth.oidc_generic.PyJWKClient", return_value=jwks_client),
        patch(
            "gsie_api.auth.oidc_generic.jwt.decode",
            side_effect=jwt_module.InvalidTokenError("non"),
        ),
        pytest.raises(InvalidOidcTokenError, match="Aucune audience OIDC valide"),
    ):
        await verifier.verify("token", "multi", "expected-nonce")


def should_reject_invalid_subject_claim() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="Sujet OIDC invalide"):
        verifier._identity_from_claims(_claims(sub=""), _PROVIDER, "expected-nonce")
    with pytest.raises(InvalidOidcTokenError, match="Sujet OIDC invalide"):
        verifier._identity_from_claims(_claims(sub="x" * 256), _PROVIDER, "expected-nonce")


def should_reject_unverified_email_claim() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="Adresse OIDC non vérifiée"):
        verifier._identity_from_claims(_claims(email_verified=False), _PROVIDER, "expected-nonce")
    with pytest.raises(InvalidOidcTokenError, match="Adresse OIDC non vérifiée"):
        verifier._identity_from_claims(_claims(email=123), _PROVIDER, "expected-nonce")


def should_reject_mismatched_nonce_claim() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with pytest.raises(InvalidOidcTokenError, match="Nonce OIDC invalide"):
        verifier._identity_from_claims(_claims(nonce="autre-nonce"), _PROVIDER, "expected-nonce")
    with pytest.raises(InvalidOidcTokenError, match="Nonce OIDC invalide"):
        verifier._identity_from_claims(_claims(nonce=None), _PROVIDER, "expected-nonce")


def should_reject_invalid_normalized_email() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    with (
        patch(
            "gsie_api.auth.oidc_generic.normalize_email",
            side_effect=InvalidEmailError("invalide"),
        ),
        pytest.raises(InvalidOidcTokenError, match="Adresse OIDC invalide"),
    ):
        verifier._identity_from_claims(_claims(), _PROVIDER, "expected-nonce")


def should_fallback_to_preferred_username_for_display_name() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    identity = verifier._identity_from_claims(
        _claims(name=None, preferred_username="jdoe"), _PROVIDER, "expected-nonce"
    )
    assert identity.display_name == "jdoe"


def should_omit_display_name_when_absent() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    identity = verifier._identity_from_claims(
        _claims(name=None, preferred_username=None), _PROVIDER, "expected-nonce"
    )
    assert identity.display_name is None


def should_omit_display_name_when_blank() -> None:
    verifier = GenericOidcVerifier((_PROVIDER,))
    identity = verifier._identity_from_claims(
        _claims(name="   ", preferred_username=None), _PROVIDER, "expected-nonce"
    )
    assert identity.display_name is None


def should_load_valid_providers_and_skip_incomplete_entries() -> None:
    settings = SimpleNamespace(
        oidc_providers=[
            {
                "name": "keycloak",
                "issuer": "https://auth.example.test",
                "jwks_url": "https://auth.example.test/certs",
                "client_ids": ["client-a", "", 12],
                "allowed_redirect_uris": [_REDIRECT, 42],
                "scopes": ["openid", 5],
                "authorization_url": "https://auth.example.test/authorize",
            },
            {"name": "", "issuer": "x", "jwks_url": "y", "client_ids": ["c"]},
            {"name": "no-issuer", "issuer": "", "jwks_url": "y", "client_ids": ["c"]},
            {"name": "no-jwks", "issuer": "x", "jwks_url": "", "client_ids": ["c"]},
            {"name": "bad-client-type", "issuer": "x", "jwks_url": "y", "client_ids": "not-a-list"},
            {"name": "empty-clients", "issuer": "x", "jwks_url": "y", "client_ids": [1, 2]},
            {
                "name": "no-scopes-no-redirects",
                "issuer": "https://auth2.example.test",
                "jwks_url": "https://auth2.example.test/certs",
                "client_ids": ["only-client"],
                "allowed_redirect_uris": "not-a-list",
                "scopes": "not-a-list",
            },
        ]
    )
    with patch("gsie_api.auth.oidc_generic.get_settings", return_value=settings):
        providers = load_oidc_providers()

    names = [p.name for p in providers]
    assert names == ["keycloak", "no-scopes-no-redirects"]

    keycloak = providers[0]
    assert keycloak.client_ids == ("client-a",)
    assert keycloak.allowed_redirect_uris == (_REDIRECT,)
    assert keycloak.scopes == ("openid",)
    assert keycloak.authorization_url == "https://auth.example.test/authorize"

    fallback = providers[1]
    assert fallback.allowed_redirect_uris == ()
    assert fallback.scopes == ("openid", "profile", "email")
    assert fallback.authorization_url is None


def should_skip_provider_entry_raising_type_error() -> None:
    class ExplodingProvider:
        def get(self, key: str, default: object = None) -> object:
            if key == "name":
                return "will-explode"
            if key == "issuer":
                return "https://auth.example.test"
            if key == "jwks_url":
                return "https://auth.example.test/certs"
            if key == "client_ids":
                raise TypeError("boom")
            return default

    settings = SimpleNamespace(oidc_providers=[ExplodingProvider()])
    with patch("gsie_api.auth.oidc_generic.get_settings", return_value=settings):
        providers = load_oidc_providers()
    assert providers == ()


def should_build_and_cache_singleton_verifier() -> None:
    oidc_generic._generic_verifier = None
    settings = SimpleNamespace(
        oidc_providers=[
            {
                "name": "keycloak",
                "issuer": "https://auth.example.test",
                "jwks_url": "https://auth.example.test/certs",
                "client_ids": ["client-a"],
            }
        ]
    )
    try:
        with patch("gsie_api.auth.oidc_generic.get_settings", return_value=settings):
            first = get_generic_oidc_verifier()
            second = get_generic_oidc_verifier()
        assert first is second
        assert first.get_provider_names() == ["keycloak"]
    finally:
        oidc_generic._generic_verifier = None
