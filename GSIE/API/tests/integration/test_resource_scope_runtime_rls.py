"""Preuve d'acceptation du RLS ``resource`` sous le profil runtime réel.

Le test ouvre une base migrée avec un LOGIN non propriétaire membre de
``gsie_application`` et explicitement ``NOBYPASSRLS``. Il reproduit ensuite
la résolution de contexte de ``get_db_resource`` avant d'éprouver directement
la policy ``resource_scope_visible``.

Invariant : INV-002 — aucun accès inter-tenant non autorisé.
Issue : #40.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from gsie_api.infrastructure.database import (
    _resolve_active_organisation,
    _resolve_active_workspace,
    set_rls_context,
)
from tests.conftest import requires_docker
from tests.integration.test_migration_baseline import (
    _IMAGE_DB,
    _REQUIRE_IMAGE,
    _image_disponible,
    _nettoyer_extensions_preinstallees,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Generator

pytestmark = requires_docker

_RUNTIME_ROLE = "gsie_runtime_rls_test"
_RUNTIME_PASSWORD = "rls_proof_only"


def _runtime_url(owner_url: str) -> str:
    _, rest = owner_url.split("://", 1)
    _, host_and_db = rest.split("@", 1)
    return (
        f"postgresql+asyncpg://{_RUNTIME_ROLE}:{_RUNTIME_PASSWORD}@"
        f"{host_and_db}"
    )


async def _execute(url: str, *statements: str) -> None:
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    finally:
        await engine.dispose()


@pytest.fixture(scope="module")
def migrated_database() -> Generator[str, None, None]:
    """Base réellement migrée jusqu'à ``head`` avec rôle runtime dédié."""
    if not _image_disponible(_IMAGE_DB):
        message = f"image {_IMAGE_DB} absente ; construire GSIE/API/Dockerfile.db"
        if _REQUIRE_IMAGE:
            pytest.fail(message)
        pytest.skip(message)

    patch = pytest.MonkeyPatch()
    container = PostgresContainer(
        image=_IMAGE_DB,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_runtime_rls",
    ).with_command(
        "postgres -c shared_preload_libraries=age -c search_path=public"
    )
    with container as postgres:
        owner_url = postgres.get_connection_url().replace(
            "postgresql+psycopg2",
            "postgresql+asyncpg",
        )
        asyncio.run(_nettoyer_extensions_preinstallees(owner_url))
        patch.setenv("GSIE_DATABASE_URL", owner_url)

        from gsie_api.core.config import get_settings

        get_settings.cache_clear()
        command.upgrade(Config("alembic.ini"), "head")
        asyncio.run(
            _execute(
                owner_url,
                f"DROP ROLE IF EXISTS {_RUNTIME_ROLE}",
                (
                    f"CREATE ROLE {_RUNTIME_ROLE} LOGIN "
                    f"PASSWORD '{_RUNTIME_PASSWORD}' NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS INHERIT"
                ),
                f"GRANT gsie_application TO {_RUNTIME_ROLE}",
            )
        )
        yield owner_url
        asyncio.run(
            _execute(
                owner_url,
                f"REASSIGN OWNED BY {_RUNTIME_ROLE} TO gsie",
                f"DROP OWNED BY {_RUNTIME_ROLE}",
                f"DROP ROLE IF EXISTS {_RUNTIME_ROLE}",
            )
        )
        get_settings.cache_clear()
    patch.undo()


@pytest.fixture(scope="module")
def tenant_ids(migrated_database: str) -> dict[str, UUID]:
    """Deux tenants, leurs workspaces et des resources représentatives."""
    ids = {
        "user_a": uuid4(),
        "user_b": uuid4(),
        "org_a": uuid4(),
        "org_b": uuid4(),
        "workspace_a": uuid4(),
        "workspace_a_other": uuid4(),
        "workspace_b": uuid4(),
        "resource_a": uuid4(),
        "resource_a_other": uuid4(),
        "resource_b": uuid4(),
        "global": uuid4(),
    }

    async def seed() -> None:
        engine = create_async_engine(migrated_database)
        try:
            async with engine.begin() as connection:
                for key in ("user_a", "user_b"):
                    await connection.execute(
                        text(
                            "INSERT INTO gsie_rgpd_identites.user_account "
                            "(id, status, session_version) "
                            "VALUES (:id, 'active', 1)"
                        ),
                        {"id": ids[key]},
                    )

                for suffix in ("a", "b"):
                    await connection.execute(
                        text(
                            "INSERT INTO gsie_organisations.organisation "
                            "(id, slug, display_name, created_by) "
                            "VALUES (:id, :slug, :name, :created_by)"
                        ),
                        {
                            "id": ids[f"org_{suffix}"],
                            "slug": f"tenant-{suffix}",
                            "name": f"Tenant {suffix.upper()}",
                            "created_by": ids[f"user_{suffix}"],
                        },
                    )
                    await connection.execute(
                        text(
                            "INSERT INTO gsie_organisations.organisation_member "
                            "(organisation_id, account_id, role, invited_by) "
                            "VALUES (:org, :account, 'owner', :account)"
                        ),
                        {
                            "org": ids[f"org_{suffix}"],
                            "account": ids[f"user_{suffix}"],
                        },
                    )

                workspaces = (
                    ("workspace_a", "org_a", "principal-a"),
                    ("workspace_a_other", "org_a", "secondaire-a"),
                    ("workspace_b", "org_b", "principal-b"),
                )
                for workspace_key, org_key, slug in workspaces:
                    await connection.execute(
                        text(
                            "INSERT INTO gsie_organisations.workspace "
                            "(id, organisation_id, slug, display_name) "
                            "VALUES (:id, :org, :slug, :name)"
                        ),
                        {
                            "id": ids[workspace_key],
                            "org": ids[org_key],
                            "slug": slug,
                            "name": slug,
                        },
                    )

                resources = (
                    (
                        "resource_a",
                        "org_a",
                        "workspace_a",
                        "tenant-a-main",
                    ),
                    (
                        "resource_a_other",
                        "org_a",
                        "workspace_a_other",
                        "tenant-a-other",
                    ),
                    (
                        "resource_b",
                        "org_b",
                        "workspace_b",
                        "tenant-b-main",
                    ),
                )
                for resource_key, org_key, workspace_key, gsie_id in resources:
                    await connection.execute(
                        text(
                            "INSERT INTO public.resource "
                            "(id, organisation_id, workspace_id, type, "
                            "gsie_id, metadata_json) "
                            "VALUES (:id, :org, :workspace, 'entity', "
                            ":gsie_id, '{}'::jsonb)"
                        ),
                        {
                            "id": ids[resource_key],
                            "org": ids[org_key],
                            "workspace": ids[workspace_key],
                            "gsie_id": gsie_id,
                        },
                    )

                await connection.execute(
                    text(
                        "INSERT INTO public.resource "
                        "(id, type, gsie_id, metadata_json) "
                        "VALUES (:id, 'entity', 'global-rls-proof', '{}'::jsonb)"
                    ),
                    {"id": ids["global"]},
                )
        finally:
            await engine.dispose()

    asyncio.run(seed())
    return ids


def _request(**headers: str) -> Request:
    raw_headers = [
        (name.lower().encode(), value.encode())
        for name, value in headers.items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": raw_headers,
        }
    )


@asynccontextmanager
async def _runtime_session(owner_url: str) -> AsyncIterator[AsyncSession]:
    engine: AsyncEngine = create_async_engine(_runtime_url(owner_url))
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with factory() as session, session.begin():
            yield session
    finally:
        await engine.dispose()


async def _activate_context(
    session: AsyncSession,
    user_id: UUID,
    organisation_id: UUID,
    workspace_id: UUID | None,
) -> tuple[str, str | None]:
    """Rejoue la résolution sécurisée utilisée par ``get_db_resource``."""
    await set_rls_context(session, str(user_id), "reader,writer")
    org_request = _request(
        **{"X-Organisation-Id": str(organisation_id)}
    )
    resolved_org = await _resolve_active_organisation(
        session,
        str(user_id),
        org_request,
    )
    assert resolved_org == str(organisation_id)

    workspace_headers = {"X-Organisation-Id": str(organisation_id)}
    if workspace_id:
        workspace_headers["X-Workspace-Id"] = str(workspace_id)
    resolved_workspace = await _resolve_active_workspace(
        session,
        resolved_org,
        _request(**workspace_headers),
        None,
    )
    await set_rls_context(
        session,
        str(user_id),
        "reader,writer",
        organisation_id=resolved_org,
        workspace_id=resolved_workspace,
    )
    return resolved_org, resolved_workspace


@pytest.mark.asyncio
async def test_runtime_role_is_non_owner_and_cannot_bypass_rls(
    migrated_database: str,
) -> None:
    engine = create_async_engine(_runtime_url(migrated_database))
    try:
        async with engine.connect() as connection:
            row = (
                await connection.execute(
                    text(
                        "SELECT r.rolsuper, r.rolbypassrls, "
                        "pg_has_role(current_user, 'gsie_application', "
                        "'member') AS app_member, "
                        "pg_get_userbyid(c.relowner) = current_user "
                        "AS owns_resource "
                        "FROM pg_roles r CROSS JOIN pg_class c "
                        "WHERE r.rolname = current_user "
                        "AND c.oid = 'public.resource'::regclass"
                    )
                )
            ).mappings().one()
        assert row["rolsuper"] is False
        assert row["rolbypassrls"] is False
        assert row["app_member"] is True
        assert row["owns_resource"] is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_foreign_organisation_header_is_rejected_before_context(
    migrated_database: str,
    tenant_ids: dict[str, UUID],
) -> None:
    async with _runtime_session(migrated_database) as session:
        await set_rls_context(
            session,
            str(tenant_ids["user_a"]),
            "reader,writer",
        )
        request = _request(
            **{"X-Organisation-Id": str(tenant_ids["org_b"])}
        )
        with pytest.raises(HTTPException) as exc_info:
            await _resolve_active_organisation(
                session,
                str(tenant_ids["user_a"]),
                request,
            )
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_runtime_rls_hides_foreign_tenant_and_other_workspace(
    migrated_database: str,
    tenant_ids: dict[str, UUID],
) -> None:
    async with _runtime_session(migrated_database) as session:
        await _activate_context(
            session,
            tenant_ids["user_a"],
            tenant_ids["org_a"],
            tenant_ids["workspace_a"],
        )
        visible = set(
            (
                await session.execute(
                    text("SELECT id FROM public.resource ORDER BY id")
                )
            ).scalars()
        )
        assert tenant_ids["resource_a"] in visible
        assert tenant_ids["global"] in visible
        assert tenant_ids["resource_a_other"] not in visible
        assert tenant_ids["resource_b"] not in visible


@pytest.mark.asyncio
async def test_runtime_cannot_soft_delete_foreign_resource(
    migrated_database: str,
    tenant_ids: dict[str, UUID],
) -> None:
    async with _runtime_session(migrated_database) as session:
        await _activate_context(
            session,
            tenant_ids["user_a"],
            tenant_ids["org_a"],
            tenant_ids["workspace_a"],
        )
        result = await session.execute(
            text(
                "UPDATE public.resource SET deleted_at = :now "
                "WHERE id = :id"
            ),
            {
                "now": datetime.now(UTC),
                "id": tenant_ids["resource_b"],
            },
        )
        assert result.rowcount == 0


@pytest.mark.asyncio
async def test_with_check_rejects_insert_claiming_foreign_scope(
    migrated_database: str,
    tenant_ids: dict[str, UUID],
) -> None:
    async with _runtime_session(migrated_database) as session:
        await _activate_context(
            session,
            tenant_ids["user_a"],
            tenant_ids["org_a"],
            tenant_ids["workspace_a"],
        )
        with pytest.raises(DBAPIError, match="row-level security|policy"):
            await session.execute(
                text(
                    "INSERT INTO public.resource "
                    "(id, organisation_id, workspace_id, type, "
                    "gsie_id, metadata_json) "
                    "VALUES (:id, :org, :workspace, 'entity', "
                    ":gsie_id, '{}'::jsonb)"
                ),
                {
                    "id": uuid4(),
                    "org": tenant_ids["org_b"],
                    "workspace": tenant_ids["workspace_b"],
                    "gsie_id": f"foreign-insert-{uuid4()}",
                },
            )


@pytest.mark.asyncio
async def test_rls_context_does_not_leak_between_transactions(
    migrated_database: str,
    tenant_ids: dict[str, UUID],
) -> None:
    engine = create_async_engine(
        _runtime_url(migrated_database),
        pool_size=1,
        max_overflow=0,
    )
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with factory() as first, first.begin():
            await _activate_context(
                first,
                tenant_ids["user_a"],
                tenant_ids["org_a"],
                tenant_ids["workspace_a"],
            )
            visible = await first.scalar(
                text(
                    "SELECT count(*) FROM public.resource "
                    "WHERE id = :id"
                ),
                {"id": tenant_ids["resource_a"]},
            )
            assert visible == 1

        # pool_size=1 force la réutilisation de la même connexion physique.
        # Le contexte transaction-local doit avoir disparu.
        async with factory() as second, second.begin():
            organisation = await second.scalar(
                text(
                    "SELECT current_setting("
                    "'app.current_organisation_id', true)"
                )
            )
            workspace = await second.scalar(
                text(
                    "SELECT current_setting("
                    "'app.current_workspace_id', true)"
                )
            )
            assert organisation in (None, "")
            assert workspace in (None, "")

            tenant_visible = await second.scalar(
                text(
                    "SELECT count(*) FROM public.resource "
                    "WHERE id = :id"
                ),
                {"id": tenant_ids["resource_a"]},
            )
            global_visible = await second.scalar(
                text(
                    "SELECT count(*) FROM public.resource "
                    "WHERE id = :id"
                ),
                {"id": tenant_ids["global"]},
            )
            assert tenant_visible == 0
            assert global_visible == 1
    finally:
        await engine.dispose()
