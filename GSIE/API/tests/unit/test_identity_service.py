"""Tests unitaires du service d'identité Quintessences (DEC-000044)."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from gsie_api.auth.identity import (
    AccountAlreadyExistsError,
    AccountLinkRequiredError,
    AuthenticatedAccount,
    GoogleIdentity,
    IdentityService,
    InvalidCredentialsError,
    LocalCredentialRecord,
    PasswordService,
    normalize_email,
)


class FakeIdentityRepository:
    """Dépôt mémoire minimal : les tests portent sur les invariants du service."""

    def __init__(self) -> None:
        self.local_credentials: dict[str, LocalCredentialRecord] = {}
        self.google_accounts: dict[tuple[str, str], AuthenticatedAccount] = {}
        self.verified_emails: set[str] = set()
        self.accounts: dict[UUID, AuthenticatedAccount] = {}
        self.last_created_local_email: str | None = None
        self.last_created_password_hash: str | None = None

    async def create_local_account(
        self,
        email: str,
        password_hash: str,
        display_name: str | None,
    ) -> AuthenticatedAccount:
        del display_name
        if email in self.local_credentials:
            raise AccountAlreadyExistsError
        account = AuthenticatedAccount(
            account_id=uuid4(),
            roles=("user",),
            provider="local",
        )
        self.last_created_local_email = email
        self.last_created_password_hash = password_hash
        self.local_credentials[email] = LocalCredentialRecord(
            account=account,
            identity_link_id=uuid4(),
            password_hash=password_hash,
        )
        self.accounts[account.account_id] = account
        return account

    async def find_local_credentials(self, email: str) -> LocalCredentialRecord | None:
        return self.local_credentials.get(email)

    async def update_password_hash(self, identity_link_id: UUID, password_hash: str) -> None:
        for email, record in self.local_credentials.items():
            if record.identity_link_id == identity_link_id:
                self.local_credentials[email] = replace(record, password_hash=password_hash)
                return

    async def mark_authenticated(self, identity_link_id: UUID) -> None:
        del identity_link_id

    async def find_provider_account(
        self,
        provider: str,
        issuer: str,
        subject: str,
    ) -> AuthenticatedAccount | None:
        assert provider == "google"
        return self.google_accounts.get((issuer, subject))

    async def has_account_with_verified_email(self, email: str) -> bool:
        return email in self.verified_emails or email in self.local_credentials

    async def create_google_account(self, identity: GoogleIdentity) -> AuthenticatedAccount:
        account = AuthenticatedAccount(
            account_id=uuid4(),
            roles=("user",),
            provider="google",
        )
        self.google_accounts[(identity.issuer, identity.subject)] = account
        self.verified_emails.add(identity.email)
        self.accounts[account.account_id] = account
        return account

    async def link_google_identity(
        self,
        account_id: UUID,
        identity: GoogleIdentity,
    ) -> AuthenticatedAccount:
        account = self.accounts[account_id]
        linked = replace(account, provider="google")
        self.google_accounts[(identity.issuer, identity.subject)] = linked
        self.verified_emails.add(identity.email)
        return linked


class FakeGoogleVerifier:
    def __init__(self, identity: GoogleIdentity) -> None:
        self.identity = identity
        self.received_token: str | None = None
        self.received_nonce: str | None = None

    @property
    def is_configured(self) -> bool:
        return True

    async def verify(self, token: str, expected_nonce: str) -> GoogleIdentity:
        self.received_token = token
        self.received_nonce = expected_nonce
        return self.identity


def _google_identity(email: str = "forestier@example.fr") -> GoogleIdentity:
    return GoogleIdentity(
        issuer="https://accounts.google.com",
        subject="google-subject-stable",
        email=email,
        display_name="Forestier Test",
    )


def should_normalize_email_without_changing_password_semantics() -> None:
    assert normalize_email("  Forestier@EXAMPLE.FR  ") == "forestier@example.fr"


def should_hash_password_with_argon2id_and_verify_it() -> None:
    passwords = PasswordService()

    password_hash = passwords.hash("mot-de-passe-long-et-unique")

    assert password_hash.startswith("$argon2id$")
    assert passwords.verify(password_hash, "mot-de-passe-long-et-unique") is True
    assert passwords.verify(password_hash, "mauvais-mot-de-passe") is False


async def should_create_canonical_account_when_local_registration_is_new() -> None:
    repository = FakeIdentityRepository()
    service = IdentityService(repository=repository, password_service=PasswordService())

    account = await service.register_local(
        email=" Forestier@Example.FR ",
        password="mot-de-passe-long-et-unique",
        display_name="Forestier Test",
    )

    assert account.provider == "local"
    assert account.roles == ("user",)
    assert repository.last_created_local_email == "forestier@example.fr"
    assert repository.last_created_password_hash is not None
    assert repository.last_created_password_hash != "mot-de-passe-long-et-unique"


async def should_refuse_duplicate_local_registration() -> None:
    repository = FakeIdentityRepository()
    service = IdentityService(repository=repository, password_service=PasswordService())
    await service.register_local(
        email="forestier@example.fr",
        password="mot-de-passe-long-et-unique",
        display_name=None,
    )

    with pytest.raises(AccountAlreadyExistsError):
        await service.register_local(
            email="FORESTIER@example.fr",
            password="autre-mot-de-passe-long",
            display_name=None,
        )


async def should_authenticate_local_account_when_password_matches() -> None:
    repository = FakeIdentityRepository()
    service = IdentityService(repository=repository, password_service=PasswordService())
    created = await service.register_local(
        email="forestier@example.fr",
        password="mot-de-passe-long-et-unique",
        display_name=None,
    )

    authenticated = await service.authenticate_local(
        email="FORESTIER@EXAMPLE.FR",
        password="mot-de-passe-long-et-unique",
    )

    assert authenticated.account_id == created.account_id


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("inconnu@example.fr", "mot-de-passe-long-et-unique"),
        ("forestier@example.fr", "mot-de-passe-incorrect"),
    ],
)
async def should_return_same_domain_error_when_local_credentials_are_invalid(
    email: str,
    password: str,
) -> None:
    repository = FakeIdentityRepository()
    service = IdentityService(repository=repository, password_service=PasswordService())
    await service.register_local(
        email="forestier@example.fr",
        password="mot-de-passe-long-et-unique",
        display_name=None,
    )

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate_local(email=email, password=password)


async def should_reuse_existing_account_when_google_subject_is_known() -> None:
    repository = FakeIdentityRepository()
    identity = _google_identity()
    existing = await repository.create_google_account(identity)
    verifier = FakeGoogleVerifier(identity)
    service = IdentityService(
        repository=repository,
        password_service=PasswordService(),
        google_verifier=verifier,
    )

    authenticated = await service.authenticate_google("id-token", "nonce-unique")

    assert authenticated.account_id == existing.account_id
    assert verifier.received_nonce == "nonce-unique"


async def should_require_explicit_link_when_google_email_matches_local_account() -> None:
    repository = FakeIdentityRepository()
    service_local = IdentityService(repository=repository, password_service=PasswordService())
    await service_local.register_local(
        email="forestier@example.fr",
        password="mot-de-passe-long-et-unique",
        display_name=None,
    )
    service_google = IdentityService(
        repository=repository,
        password_service=PasswordService(),
        google_verifier=FakeGoogleVerifier(_google_identity()),
    )

    with pytest.raises(AccountLinkRequiredError):
        await service_google.authenticate_google("id-token", "nonce-unique")


async def should_create_google_account_when_subject_and_email_are_new() -> None:
    repository = FakeIdentityRepository()
    identity = _google_identity("nouveau@example.fr")
    service = IdentityService(
        repository=repository,
        password_service=PasswordService(),
        google_verifier=FakeGoogleVerifier(identity),
    )

    account = await service.authenticate_google("id-token", "nonce-unique")

    assert account.provider == "google"
    assert repository.google_accounts[(identity.issuer, identity.subject)].account_id == (
        account.account_id
    )


async def should_link_google_only_to_authenticated_canonical_account() -> None:
    repository = FakeIdentityRepository()
    local_service = IdentityService(repository=repository, password_service=PasswordService())
    local_account = await local_service.register_local(
        email="forestier@example.fr",
        password="mot-de-passe-long-et-unique",
        display_name=None,
    )
    identity = _google_identity()
    service = IdentityService(
        repository=repository,
        password_service=PasswordService(),
        google_verifier=FakeGoogleVerifier(identity),
    )

    linked = await service.link_google(
        account_id=local_account.account_id,
        token="id-token",
        nonce="nonce-unique",
    )

    assert linked.account_id == local_account.account_id
    assert repository.google_accounts[(identity.issuer, identity.subject)].account_id == (
        local_account.account_id
    )
