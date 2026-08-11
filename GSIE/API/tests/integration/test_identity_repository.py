"""Intégration PostgreSQL du dépôt d'identité Quintessences."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import pytest

from gsie_api.auth.identity import AccountAlreadyExistsError, GoogleIdentity
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from tests.conftest import requires_docker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = requires_docker


async def should_persist_and_authenticate_local_identity(db_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(db_session)

    created = await repository.create_local_account(
        email="forestier@example.fr",
        password_hash="$argon2id$hash-de-test",
        display_name="Forestier Test",
    )
    credentials = await repository.find_local_credentials("forestier@example.fr")

    assert isinstance(created.account_id, UUID)
    assert created.roles == ("user",)
    assert credentials is not None
    assert credentials.account.account_id == created.account_id
    assert credentials.password_hash == "$argon2id$hash-de-test"


async def should_refuse_second_account_for_same_local_email(db_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(db_session)
    await repository.create_local_account(
        email="forestier@example.fr",
        password_hash="$argon2id$premier",
        display_name=None,
    )

    with pytest.raises(AccountAlreadyExistsError):
        await repository.create_local_account(
            email="forestier@example.fr",
            password_hash="$argon2id$second",
            display_name=None,
        )


async def should_keep_google_subject_as_external_identity_key(db_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(db_session)
    identity = GoogleIdentity(
        issuer="https://accounts.google.com",
        subject="stable-subject",
        email="forestier@example.fr",
        display_name="Forestier Test",
    )

    created = await repository.create_google_account(identity)
    found = await repository.find_provider_account(
        provider="google",
        issuer=identity.issuer,
        subject=identity.subject,
    )

    assert found is not None
    assert found.account_id == created.account_id
    assert await repository.has_account_with_verified_email(identity.email) is True


async def should_link_google_to_existing_canonical_account(db_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(db_session)
    local = await repository.create_local_account(
        email="forestier@example.fr",
        password_hash="$argon2id$hash-de-test",
        display_name=None,
    )
    identity = GoogleIdentity(
        issuer="https://accounts.google.com",
        subject="stable-subject",
        email="forestier@example.fr",
        display_name="Forestier Test",
    )

    linked = await repository.link_google_identity(local.account_id, identity)
    found = await repository.find_provider_account("google", identity.issuer, identity.subject)

    assert linked.account_id == local.account_id
    assert found is not None
    assert found.account_id == local.account_id
