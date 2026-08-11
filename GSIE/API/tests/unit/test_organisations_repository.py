"""Tests unitaires du dépôt SQLAlchemy des organisations.

Utilise SQLite in-memory (aiosqlite) pour tester le dépôt sans Docker, comme
``tests/unit/test_service.py``. Les schémas PostgreSQL sont simulés par des
bases SQLite attachées (``ATTACH DATABASE``). Valide le comportement réel de
``SqlAlchemyOrganisationRepository`` : contraintes d'unicité, soft-delete,
pagination, réactivation d'un membre révoqué, invitations à usage unique.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from gsie_api.infrastructure.models import Base
from gsie_api.infrastructure.models.accounts import IdentityProviderLinkModel, UserAccountModel
from gsie_api.organisations.repository import SqlAlchemyOrganisationRepository
from gsie_api.organisations.service import (
    AlreadyMemberError,
    NotMemberError,
    SlugAlreadyTakenError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@compiles(JSONB, "sqlite")
def _jsonb_to_sqlite(element: Any, compiler: Any, **kw: Any) -> str:
    """JSONB → JSON en SQLite (voir tests/unit/test_service.py)."""
    return "JSON"


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Session SQLite in-memory avec le schéma organisations + accounts créé."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    from sqlalchemy.sql.schema import DefaultClause

    replaced: list[tuple[Any, str, Any]] = []
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.server_default is not None:
                sd = col.server_default
                sd_arg = getattr(sd, "arg", sd)
                if str(sd_arg) == "now()":
                    replaced.append((col, "server_default", col.server_default))
                    col.server_default = DefaultClause(func.now())
                elif not isinstance(sd_arg, str) and getattr(sd_arg, "name", "") == "text":
                    replaced.append((col, "server_default", col.server_default))
                    col.server_default = DefaultClause("'{}'")
            if col.onupdate is not None:
                replaced.append((col, "onupdate", col.onupdate))
                col.onupdate = None

    async with engine.begin() as conn:
        for schema in sorted(
            {table.schema for table in Base.metadata.tables.values() if table.schema}
        ):
            await conn.exec_driver_sql(f"ATTACH DATABASE ':memory:' AS {schema}")

        from geoalchemy2 import Geometry

        tables_to_create = [
            t
            for t in Base.metadata.sorted_tables
            if not any(isinstance(c.type, Geometry) for c in t.columns)
        ]
        await conn.run_sync(Base.metadata.create_all, tables=tables_to_create)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as s:
        yield s

    for col, attr_name, original in replaced:
        setattr(col, attr_name, original)

    await engine.dispose()


@pytest.fixture
def repo(session: AsyncSession) -> SqlAlchemyOrganisationRepository:
    return SqlAlchemyOrganisationRepository(session)


async def _make_account(session: AsyncSession, *, verified_email: str | None = None) -> Any:
    """Crée un compte (et éventuellement un lien vérifié) pour satisfaire les FK."""
    account = UserAccountModel(id=uuid4(), display_name="Forestier")
    session.add(account)
    await session.flush()
    if verified_email is not None:
        link = IdentityProviderLinkModel(
            id=uuid4(),
            account_id=account.id,
            provider="local",
            issuer="gsie",
            subject=str(account.id),
            email_normalized=verified_email,
            email_verified=True,
        )
        session.add(link)
        await session.flush()
    return account


# ---------------------------------------------------------------------------
# create_organisation / get_organisation_by_slug / get_organisation
# ---------------------------------------------------------------------------


async def should_create_organisation_and_read_it_back(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)

    record = await repo.create_organisation("onf", "ONF", account.id)

    assert record.slug == "onf"
    assert record.status == "active"
    fetched = await repo.get_organisation(record.id)
    assert fetched is not None
    assert fetched.slug == "onf"


async def should_raise_slug_taken_when_creating_organisation_with_duplicate_slug(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    await repo.create_organisation("onf", "ONF", account.id)

    with pytest.raises(SlugAlreadyTakenError):
        await repo.create_organisation("onf", "Autre ONF", account.id)


async def should_return_none_when_organisation_by_slug_not_found(
    repo: SqlAlchemyOrganisationRepository,
) -> None:
    assert await repo.get_organisation_by_slug("inconnu") is None


async def should_return_none_when_organisation_soft_deleted(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    record = await repo.create_organisation("onf", "ONF", account.id)
    from gsie_api.infrastructure.models.organisations import OrganisationModel

    model = await session.get(OrganisationModel, record.id)
    assert model is not None
    model.deleted_at = datetime.now(UTC)
    await session.flush()

    assert await repo.get_organisation(record.id) is None
    assert await repo.get_organisation_by_slug("onf") is None


async def should_return_none_when_organisation_not_found_by_id(
    repo: SqlAlchemyOrganisationRepository,
) -> None:
    assert await repo.get_organisation(uuid4()) is None


# ---------------------------------------------------------------------------
# list_organisations_for_account
# ---------------------------------------------------------------------------


async def should_list_organisations_visible_by_creator_or_member(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    creator = await _make_account(session)
    member_account = await _make_account(session)
    stranger = await _make_account(session)
    org1 = await repo.create_organisation("onf", "ONF", creator.id)
    org2 = await repo.create_organisation("cnpf", "CNPF", creator.id)
    await repo.add_member(org2.id, member_account.id, "member", creator.id)
    # Une organisation dont ni le créateur ni membre ne sont "stranger"
    del stranger

    records, total = await repo.list_organisations_for_account(
        member_account.id, offset=0, limit=10
    )

    assert total == 1
    assert records[0].id == org2.id

    records_creator, total_creator = await repo.list_organisations_for_account(
        creator.id, offset=0, limit=10
    )
    assert total_creator == 2
    assert {r.id for r in records_creator} == {org1.id, org2.id}


async def should_paginate_organisations_list(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    await repo.create_organisation("onf", "ONF", account.id)
    await repo.create_organisation("cnpf", "CNPF", account.id)
    await repo.create_organisation("irstea", "IRSTEA", account.id)

    page, total = await repo.list_organisations_for_account(account.id, offset=0, limit=2)
    assert total == 3
    assert len(page) == 2


# ---------------------------------------------------------------------------
# create_workspace / get_workspace / list_workspaces
# ---------------------------------------------------------------------------


async def should_create_workspace_and_read_it_back(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", account.id)

    ws = await repo.create_workspace(org.id, "ws1", "Workspace 1")

    assert ws.organisation_id == org.id
    fetched = await repo.get_workspace(org.id, ws.id)
    assert fetched is not None
    assert fetched.slug == "ws1"


async def should_raise_slug_taken_when_creating_workspace_with_duplicate_slug_in_same_org(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", account.id)
    await repo.create_workspace(org.id, "ws1", "Workspace 1")

    with pytest.raises(SlugAlreadyTakenError):
        await repo.create_workspace(org.id, "ws1", "Autre Workspace")


async def should_allow_same_workspace_slug_in_different_organisations(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    org1 = await repo.create_organisation("onf", "ONF", account.id)
    org2 = await repo.create_organisation("cnpf", "CNPF", account.id)

    ws1 = await repo.create_workspace(org1.id, "ws1", "Workspace 1")
    ws2 = await repo.create_workspace(org2.id, "ws1", "Workspace 1")

    assert ws1.id != ws2.id


async def should_return_none_when_workspace_not_found(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", account.id)

    assert await repo.get_workspace(org.id, uuid4()) is None


async def should_return_none_when_workspace_soft_deleted(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", account.id)
    ws = await repo.create_workspace(org.id, "ws1", "Workspace 1")
    from gsie_api.infrastructure.models.organisations import WorkspaceModel

    model = await session.get(WorkspaceModel, ws.id)
    assert model is not None
    model.deleted_at = datetime.now(UTC)
    await session.flush()

    assert await repo.get_workspace(org.id, ws.id) is None


async def should_paginate_workspaces_list(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", account.id)
    await repo.create_workspace(org.id, "ws1", "Workspace 1")
    await repo.create_workspace(org.id, "ws2", "Workspace 2")

    page, total = await repo.list_workspaces(org.id, offset=0, limit=1)

    assert total == 2
    assert len(page) == 1


# ---------------------------------------------------------------------------
# add_member / get_member / list_members / revoke_member / count_owners
# ---------------------------------------------------------------------------


async def should_add_member_and_read_it_back(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    member_account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)

    member = await repo.add_member(org.id, member_account.id, "member", owner.id)

    assert member.role == "member"
    fetched = await repo.get_member(org.id, member_account.id)
    assert fetched is not None
    assert fetched.account_id == member_account.id


async def should_raise_already_member_when_adding_active_member_twice(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    member_account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)
    await repo.add_member(org.id, member_account.id, "member", owner.id)

    with pytest.raises(AlreadyMemberError):
        await repo.add_member(org.id, member_account.id, "admin", owner.id)


async def should_reactivate_revoked_member_on_add_member(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    member_account = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)
    await repo.add_member(org.id, member_account.id, "member", owner.id)
    await repo.revoke_member(org.id, member_account.id)

    reactivated = await repo.add_member(org.id, member_account.id, "admin", owner.id)

    assert reactivated.revoked_at is None
    assert reactivated.role == "admin"


async def should_return_none_when_member_not_found(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)

    assert await repo.get_member(org.id, uuid4()) is None


async def should_list_members_excluding_revoked(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    m1 = await _make_account(session)
    m2 = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)
    await repo.add_member(org.id, owner.id, "owner", owner.id)
    await repo.add_member(org.id, m1.id, "member", owner.id)
    await repo.add_member(org.id, m2.id, "member", owner.id)
    await repo.revoke_member(org.id, m2.id)

    members, total = await repo.list_members(org.id, offset=0, limit=10)

    assert total == 2  # owner + m1 (m2 révoqué exclu)
    assert m2.id not in {m.account_id for m in members}


async def should_raise_not_member_when_revoking_unknown_member(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)

    with pytest.raises(NotMemberError):
        await repo.revoke_member(org.id, uuid4())


async def should_count_only_active_owners(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner1 = await _make_account(session)
    owner2 = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner1.id)
    await repo.add_member(org.id, owner1.id, "owner", owner1.id)
    await repo.add_member(org.id, owner2.id, "owner", owner1.id)

    assert await repo.count_owners(org.id) == 2

    await repo.revoke_member(org.id, owner2.id)
    assert await repo.count_owners(org.id) == 1


# ---------------------------------------------------------------------------
# create_invitation / get_pending_invitation / mark_invitation_accepted
# ---------------------------------------------------------------------------


async def should_create_invitation_and_read_it_back_pending(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)
    expires_at = datetime.now(UTC) + timedelta(hours=72)

    invitation = await repo.create_invitation(
        org.id, "membre@example.fr", "member", owner.id, "hash123", expires_at
    )

    assert invitation.email_normalized == "membre@example.fr"
    pending = await repo.get_pending_invitation("hash123")
    assert pending is not None
    assert pending.id == invitation.id


async def should_return_none_when_pending_invitation_not_found(
    repo: SqlAlchemyOrganisationRepository,
) -> None:
    assert await repo.get_pending_invitation("unknown-hash") is None


async def should_return_none_when_invitation_already_accepted(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)
    expires_at = datetime.now(UTC) + timedelta(hours=72)
    invitation = await repo.create_invitation(
        org.id, "membre@example.fr", "member", owner.id, "hash456", expires_at
    )

    await repo.mark_invitation_accepted(invitation.id)

    assert await repo.get_pending_invitation("hash456") is None


async def should_raise_already_member_when_marking_invitation_accepted_twice(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    owner = await _make_account(session)
    org = await repo.create_organisation("onf", "ONF", owner.id)
    expires_at = datetime.now(UTC) + timedelta(hours=72)
    invitation = await repo.create_invitation(
        org.id, "membre@example.fr", "member", owner.id, "hash789", expires_at
    )
    await repo.mark_invitation_accepted(invitation.id)

    with pytest.raises(AlreadyMemberError):
        await repo.mark_invitation_accepted(invitation.id)


# ---------------------------------------------------------------------------
# get_verified_emails
# ---------------------------------------------------------------------------


async def should_return_only_verified_non_revoked_emails(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session, verified_email="verifie@example.fr")
    # Lien non vérifié — doit être exclu.
    unverified_link = IdentityProviderLinkModel(
        id=uuid4(),
        account_id=account.id,
        provider="google",
        issuer="google",
        subject="google-sub",
        email_normalized="non-verifie@example.fr",
        email_verified=False,
    )
    # Lien vérifié mais révoqué — doit être exclu.
    revoked_link = IdentityProviderLinkModel(
        id=uuid4(),
        account_id=account.id,
        provider="oidc",
        issuer="oidc-issuer",
        subject="oidc-sub",
        email_normalized="revoque@example.fr",
        email_verified=True,
        revoked_at=datetime.now(UTC),
    )
    session.add_all([unverified_link, revoked_link])
    await session.flush()

    emails = await repo.get_verified_emails(account.id)

    assert emails == ("verifie@example.fr",)


async def should_return_empty_tuple_when_no_verified_emails(
    repo: SqlAlchemyOrganisationRepository, session: AsyncSession
) -> None:
    account = await _make_account(session)
    assert await repo.get_verified_emails(account.id) == ()


# ---------------------------------------------------------------------------
# add_member — insertion concurrente (IntegrityError sur flush)
# ---------------------------------------------------------------------------
#
# Ce cas (deux requêtes concurrentes gagnant toutes deux la vérification
# `session.get(..., with_for_update=True)` avant qu'aucune n'ait encore
# inséré) exige deux connexions/transactions séparées agissant réellement en
# parallèle — irreproductible de façon déterministe avec une session SQLite
# unique dans un test synchrone. On isole donc cette seule branche avec une
# session mockée, pour vérifier que le dépôt traduit bien l'IntegrityError du
# second flush en ``AlreadyMemberError`` et effectue un rollback.


async def should_raise_already_member_when_concurrent_insert_violates_unique_constraint() -> None:
    """Simule une course : `get` ne voit rien, mais `flush` échoue (contrainte
    unique déjà posée par une transaction concurrente)."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()  # Session.add() est synchrone, pas une coroutine.
    mock_session.get.return_value = None
    mock_session.flush.side_effect = IntegrityError("INSERT", {}, Exception("unique violation"))
    repo = SqlAlchemyOrganisationRepository(mock_session)

    with pytest.raises(AlreadyMemberError):
        await repo.add_member(uuid4(), uuid4(), "member", uuid4())

    mock_session.rollback.assert_awaited_once()
