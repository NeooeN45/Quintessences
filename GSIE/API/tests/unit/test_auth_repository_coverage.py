"""Couverture résiduelle de ``SqlAlchemyIdentityRepository`` (auth/repository.py).

Ces tests s'exécutent sur une session SQLite en mémoire (fixture
``identity_sqlite_session``) plutôt que sur le PostgreSQL réel de
``tests/integration/test_identity_repository.py`` : les tables du schéma
d'identité n'utilisent que des types portables (UUID, String, DateTime,
Boolean, Integer), donc SQLite exerce le même SQL réel (contraintes UNIQUE,
IntegrityError, verrous FOR UPDATE en no-op) sans dépendre de Docker. Cela
couvre les branches d'erreur métier (comptes absents, révoqués, codes
expirés/invalides) qui étaient jusqu'ici non exercées.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from sqlalchemy import select

from gsie_api.auth.identity import AuthenticatedAccount, GoogleIdentity, InvalidCredentialsError
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from gsie_api.infrastructure.models.accounts import IdentityProviderLinkModel, UserAccountModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_HASHER = PasswordHasher()


# ---------------------------------------------------------------------------
# find_account_id_for_email — lignes 280-294
# ---------------------------------------------------------------------------


async def should_find_account_id_for_active_local_email(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created = await repository.create_local_account("forestier@example.fr", "hash", None)

    account_id = await repository.find_account_id_for_email("forestier@example.fr")

    assert account_id == created.account_id


async def should_return_none_for_unknown_email(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)

    assert await repository.find_account_id_for_email("inconnu@example.fr") is None


# ---------------------------------------------------------------------------
# mark_deletion_requested / cancel_deletion — lignes 395-417
# ---------------------------------------------------------------------------


async def should_mark_deletion_requested_and_bump_session_version(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created = await repository.create_local_account("forestier@example.fr", "hash", None)
    now = datetime.now(UTC)

    await repository.mark_deletion_requested(created.account_id, now, now + timedelta(days=30))

    account = await identity_sqlite_session.get(UserAccountModel, created.account_id)
    assert account is not None
    assert account.status == "pending_deletion"
    assert account.session_version == 2


async def should_raise_when_marking_deletion_for_unknown_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    now = datetime.now(UTC)

    with pytest.raises(InvalidCredentialsError):
        await repository.mark_deletion_requested(uuid4(), now, now + timedelta(days=30))


async def should_raise_when_marking_deletion_twice(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created = await repository.create_local_account("forestier@example.fr", "hash", None)
    now = datetime.now(UTC)
    await repository.mark_deletion_requested(created.account_id, now, now + timedelta(days=30))

    with pytest.raises(InvalidCredentialsError):
        await repository.mark_deletion_requested(created.account_id, now, now + timedelta(days=30))


async def should_cancel_deletion_and_restore_active_status(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created = await repository.create_local_account("forestier@example.fr", "hash", None)
    now = datetime.now(UTC)
    await repository.mark_deletion_requested(created.account_id, now, now + timedelta(days=30))

    await repository.cancel_deletion(created.account_id)

    account = await identity_sqlite_session.get(UserAccountModel, created.account_id)
    assert account is not None
    assert account.status == "active"
    assert account.deletion_requested_at is None
    assert account.deletion_scheduled_at is None
    assert account.session_version == 3


async def should_noop_when_cancelling_deletion_on_active_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    """Un compte déjà actif n'a rien à annuler — pas d'erreur, pas d'effet."""
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created = await repository.create_local_account("forestier@example.fr", "hash", None)

    await repository.cancel_deletion(created.account_id)

    account = await identity_sqlite_session.get(UserAccountModel, created.account_id)
    assert account is not None
    assert account.status == "active"
    assert account.session_version == 1


async def should_raise_when_cancelling_deletion_for_unknown_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)

    with pytest.raises(InvalidCredentialsError):
        await repository.cancel_deletion(uuid4())


async def should_raise_when_cancelling_deletion_for_deleted_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created = await repository.create_local_account("forestier@example.fr", "hash", None)
    account = await identity_sqlite_session.get(UserAccountModel, created.account_id)
    assert account is not None
    account.deleted_at = datetime.now(UTC)
    await identity_sqlite_session.flush()

    with pytest.raises(InvalidCredentialsError):
        await repository.cancel_deletion(created.account_id)


# ---------------------------------------------------------------------------
# get_local_password_hash — lignes 419-432
# ---------------------------------------------------------------------------


async def should_get_local_password_hash_for_local_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    await repository.create_local_account("forestier@example.fr", "$argon2id$hash", None)

    account_id = await repository.find_local_account_id("forestier@example.fr")
    assert account_id is not None

    password_hash = await repository.get_local_password_hash(account_id)

    assert password_hash == "$argon2id$hash"


async def should_return_none_password_hash_for_google_only_account(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    identity = GoogleIdentity(
        issuer="https://accounts.google.com",
        subject="stable-subject",
        email="forestier@example.fr",
        display_name=None,
    )
    created = await repository.create_google_account(identity)

    assert await repository.get_local_password_hash(created.account_id) is None


# ---------------------------------------------------------------------------
# Changement d'e-mail — lignes 434-524
# ---------------------------------------------------------------------------


async def _create_account_with_email(
    repository: SqlAlchemyIdentityRepository,
) -> tuple[AuthenticatedAccount, str, str]:
    created = await repository.create_local_account("forestier@example.fr", "hash", None)
    return created, "forestier@example.fr", "nouveau@example.fr"


async def should_replace_and_fetch_active_email_change_request(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)

    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )

    assert request.current_email == current_email
    assert request.new_email == new_email
    assert request.current_confirmed is False
    assert request.new_confirmed is False

    active = await repository.get_active_email_change_request(created.account_id)
    assert active is not None
    assert active.request_id == request.request_id


async def should_replace_previous_pending_email_change_request(
    identity_sqlite_session: AsyncSession,
) -> None:
    """Une nouvelle demande remplace toute demande active précédente."""
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, _ = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)

    first = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        "premier@example.fr",
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )
    second = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        "second@example.fr",
        _HASHER.hash("3333"),
        _HASHER.hash("4444"),
        expires_at,
    )

    active = await repository.get_active_email_change_request(created.account_id)
    assert active is not None
    assert active.request_id == second.request_id
    assert active.request_id != first.request_id


async def should_return_none_when_no_active_email_change_request(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, _current, _new = await _create_account_with_email(repository)

    assert await repository.get_active_email_change_request(created.account_id) is None


async def should_confirm_email_change_code_on_each_channel(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )

    confirmed_current = await repository.confirm_email_change_code(
        request.request_id, "current", "1111"
    )
    assert confirmed_current is not None
    assert confirmed_current.current_confirmed is True
    assert confirmed_current.new_confirmed is False

    confirmed_new = await repository.confirm_email_change_code(request.request_id, "new", "2222")
    assert confirmed_new is not None
    assert confirmed_new.current_confirmed is True
    assert confirmed_new.new_confirmed is True


async def should_return_none_when_email_change_code_is_wrong(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )

    result = await repository.confirm_email_change_code(request.request_id, "current", "0000")

    assert result is None


async def should_return_none_when_email_change_request_unknown(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)

    assert await repository.confirm_email_change_code(uuid4(), "current", "1111") is None


async def should_return_none_when_email_change_request_expired(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expired_at = datetime.now(UTC) - timedelta(minutes=1)
    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expired_at,
    )

    result = await repository.confirm_email_change_code(request.request_id, "current", "1111")

    assert result is None


async def should_complete_email_change_and_update_identity_link(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )
    await repository.confirm_email_change_code(request.request_id, "current", "1111")
    await repository.confirm_email_change_code(request.request_id, "new", "2222")

    await repository.complete_email_change(request.request_id)

    account = await identity_sqlite_session.get(UserAccountModel, created.account_id)
    assert account is not None
    assert account.session_version == 2
    credentials = await repository.find_local_credentials(new_email)
    assert credentials is not None
    assert credentials.account.account_id == created.account_id


async def should_raise_when_completing_unknown_email_change_request(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)

    with pytest.raises(InvalidCredentialsError):
        await repository.complete_email_change(uuid4())


async def should_raise_when_completing_email_change_missing_confirmations(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )
    # Une seule des deux confirmations est faite.
    await repository.confirm_email_change_code(request.request_id, "current", "1111")

    with pytest.raises(InvalidCredentialsError):
        await repository.complete_email_change(request.request_id)


async def should_raise_when_completing_email_change_without_active_local_link(
    identity_sqlite_session: AsyncSession,
) -> None:
    """Un lien local révoqué entre les deux confirmations bloque la complétion."""
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    created, current_email, new_email = await _create_account_with_email(repository)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    request = await repository.replace_email_change_request(
        created.account_id,
        current_email,
        new_email,
        _HASHER.hash("1111"),
        _HASHER.hash("2222"),
        expires_at,
    )
    await repository.confirm_email_change_code(request.request_id, "current", "1111")
    await repository.confirm_email_change_code(request.request_id, "new", "2222")

    link_statement = select(IdentityProviderLinkModel).where(
        IdentityProviderLinkModel.account_id == created.account_id,
        IdentityProviderLinkModel.provider == "local",
    )
    link = (await identity_sqlite_session.execute(link_statement)).scalar_one()
    link.revoked_at = datetime.now(UTC)
    await identity_sqlite_session.flush()

    with pytest.raises(InvalidCredentialsError):
        await repository.complete_email_change(request.request_id)


# ---------------------------------------------------------------------------
# MFA TOTP — lignes 581-649
# ---------------------------------------------------------------------------


async def should_return_none_active_secret_when_none_configured(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    account_id = uuid4()

    assert await repository.get_active_secret(account_id) is None


async def should_save_and_fetch_active_mfa_secret(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    account_id = uuid4()

    await repository.save_secret(account_id, "cipher-text")
    record = await repository.get_active_secret(account_id)

    assert record is not None
    assert record.account_id == account_id
    assert record.secret_cipher == "cipher-text"


async def should_disable_mfa_secret(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.save_secret(account_id, "cipher-text")

    await repository.disable_secret(account_id)

    assert await repository.get_active_secret(account_id) is None


async def should_replace_recovery_codes_on_save(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    account_id = uuid4()
    first_code = _HASHER.hash("AAAA1111")
    await repository.save_recovery_codes(account_id, [first_code])
    assert await repository.has_recovery_codes(account_id) is True

    second_code = _HASHER.hash("BBBB2222")
    await repository.save_recovery_codes(account_id, [second_code])

    assert await repository.has_recovery_codes(account_id) is True
    assert await repository.consume_recovery_code(account_id, "AAAA1111") is False
    assert await repository.consume_recovery_code(account_id, "BBBB2222") is True


async def should_consume_recovery_code_once(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.save_recovery_codes(account_id, [_HASHER.hash("AAAA1111")])

    assert await repository.consume_recovery_code(account_id, "AAAA1111") is True
    assert await repository.consume_recovery_code(account_id, "AAAA1111") is False


async def should_reject_invalid_recovery_code(identity_sqlite_session: AsyncSession) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)
    account_id = uuid4()
    await repository.save_recovery_codes(account_id, [_HASHER.hash("AAAA1111")])

    assert await repository.consume_recovery_code(account_id, "WRONGCODE") is False


async def should_report_no_recovery_codes_when_none_saved(
    identity_sqlite_session: AsyncSession,
) -> None:
    repository = SqlAlchemyIdentityRepository(identity_sqlite_session)

    assert await repository.has_recovery_codes(uuid4()) is False
