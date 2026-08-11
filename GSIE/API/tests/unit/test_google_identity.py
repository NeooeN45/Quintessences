"""Tests de validation Google OIDC et des nonces à usage unique."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from gsie_api.auth.google_identity import GoogleTokenVerifier, InvalidGoogleTokenError
from gsie_api.auth.google_nonces import MemoryGoogleNonceStore

if TYPE_CHECKING:
    from collections.abc import Mapping


async def should_consume_google_nonce_only_once() -> None:
    store = MemoryGoogleNonceStore(ttl_seconds=300)
    nonce = await store.create()

    assert await store.consume(nonce) is True
    assert await store.consume(nonce) is False


async def should_validate_google_identity_using_stable_subject() -> None:
    async def verify_token(token: str, audience: str) -> Mapping[str, object]:
        assert token == "google-id-token"
        assert audience == "web-client-id"
        return {
            "iss": "https://accounts.google.com",
            "sub": "stable-google-subject",
            "aud": audience,
            "email": "Forestier@Example.FR",
            "email_verified": True,
            "name": "Forestier Test",
            "nonce": "nonce-attendu",
        }

    verifier = GoogleTokenVerifier(
        client_ids=("web-client-id",),
        verify_token=verify_token,
    )

    identity = await verifier.verify("google-id-token", "nonce-attendu")

    assert identity.subject == "stable-google-subject"
    assert identity.email == "forestier@example.fr"
    assert identity.issuer == "https://accounts.google.com"


@pytest.mark.parametrize(
    "claims",
    [
        {"iss": "https://accounts.google.com", "sub": "", "email_verified": True},
        {
            "iss": "https://accounts.google.com",
            "sub": "subject",
            "email": "forestier@example.fr",
            "email_verified": False,
            "nonce": "nonce-attendu",
        },
        {
            "iss": "https://accounts.google.com",
            "sub": "subject",
            "email": "forestier@example.fr",
            "email_verified": True,
            "nonce": "autre-nonce",
        },
        {
            "iss": "https://accounts.google.com",
            "sub": "subject",
            "email": "adresse-invalide",
            "email_verified": True,
            "nonce": "nonce-attendu",
        },
    ],
)
async def should_reject_google_claims_when_required_identity_guarantee_is_missing(
    claims: Mapping[str, object],
) -> None:
    async def verify_token(token: str, audience: str) -> Mapping[str, object]:
        del token, audience
        return claims

    verifier = GoogleTokenVerifier(
        client_ids=("web-client-id",),
        verify_token=verify_token,
    )

    with pytest.raises(InvalidGoogleTokenError):
        await verifier.verify("google-id-token", "nonce-attendu")


async def should_reject_google_login_when_no_client_id_is_configured() -> None:
    verifier = GoogleTokenVerifier(client_ids=())

    assert verifier.is_configured is False
    with pytest.raises(InvalidGoogleTokenError, match="non configuré"):
        await verifier.verify("google-id-token", "nonce-attendu")
