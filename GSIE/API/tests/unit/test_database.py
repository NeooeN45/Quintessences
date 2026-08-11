"""Tests unitaires — base de données (infrastructure/database.py)."""

import contextlib
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from gsie_api.core.config import Settings
from gsie_api.infrastructure.database import (
    _build_engine_kwargs,
    _resolve_active_organisation,
    _resolve_active_workspace,
    get_db,
    get_db_resource,
    get_db_rls,
    get_db_user_rls,
    set_rls_context,
)


def should_include_basic_kwargs_when_building_engine():
    """_build_engine_kwargs doit inclure echo, pool_size, max_overflow, pool_pre_ping."""
    settings = Settings(
        db_echo=True,
        db_pool_size=10,
        db_max_overflow=5,
        db_pgbouncer_mode=False,
        db_ssl_mode="disable",
    )
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["echo"] is True
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 5
    assert kwargs["pool_pre_ping"] is True
    assert "connect_args" not in kwargs


def should_disable_prepared_statements_when_pgbouncer_mode():
    """_build_engine_kwargs doit désactiver les prepared statements en mode PgBouncer."""
    settings = Settings(db_pgbouncer_mode=True, db_ssl_mode="disable")
    kwargs = _build_engine_kwargs(settings)
    assert "connect_args" in kwargs
    assert kwargs["connect_args"]["statement_cache_size"] == 0
    assert kwargs["connect_args"]["prepared_statement_cache_size"] == 0


def should_not_include_connect_args_when_no_pgbouncer():
    """_build_engine_kwargs ne doit pas inclure connect_args sans PgBouncer ni TLS."""
    settings = Settings(db_pgbouncer_mode=False, db_ssl_mode="disable")
    kwargs = _build_engine_kwargs(settings)
    assert "connect_args" not in kwargs


def should_include_ssl_connect_arg_by_default():
    """_build_engine_kwargs doit activer TLS (mode 'prefer') par défaut."""
    settings = Settings(db_pgbouncer_mode=False)
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["connect_args"]["ssl"] == "prefer"


def should_include_ssl_require_in_production_mode():
    """_build_engine_kwargs doit propager db_ssl_mode='require' vers asyncpg."""
    settings = Settings(db_ssl_mode="require")
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["connect_args"]["ssl"] == "require"


def should_combine_pgbouncer_and_ssl_connect_args():
    """_build_engine_kwargs doit combiner PgBouncer et TLS dans connect_args."""
    settings = Settings(db_pgbouncer_mode=True, db_ssl_mode="require")
    kwargs = _build_engine_kwargs(settings)
    assert kwargs["connect_args"]["statement_cache_size"] == 0
    assert kwargs["connect_args"]["ssl"] == "require"


@pytest.mark.asyncio
async def should_rollback_when_exception_raised():
    """get_db doit rollback en cas d'exception pendant la session."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
    mock_session.rollback = AsyncMock()

    # Mock du context manager async : async_session_factory() doit retourner
    # un objet qui supporte __aenter__ et __aexit__
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_ctx)

    import gsie_api.infrastructure.database as db_module

    original_factory = db_module.async_session_factory
    db_module.async_session_factory = mock_factory

    try:
        gen = get_db()
        await gen.__anext__()  # yield session
        with contextlib.suppress(Exception):
            await gen.__anext__()  # commit → exception → rollback
        mock_session.rollback.assert_called_once()
    finally:
        db_module.async_session_factory = original_factory


@pytest.mark.asyncio
async def should_set_rls_context_with_user_id_and_roles():
    """set_rls_context doit exécuter SET LOCAL avec user_id et roles."""
    mock_session = AsyncMock()
    await set_rls_context(mock_session, "user-uuid-123", "admin,researcher")
    assert mock_session.execute.call_count == 2
    # Premier appel : SET LOCAL app.current_user_id
    first_call = mock_session.execute.call_args_list[0]
    assert "app.current_user_id" in first_call.args[0].text
    assert first_call.args[1]["uid"] == "user-uuid-123"
    # Second appel : SET LOCAL app.current_user_roles
    second_call = mock_session.execute.call_args_list[1]
    assert "app.current_user_roles" in second_call.args[0].text
    assert second_call.args[1]["roles"] == "admin,researcher"


@pytest.mark.asyncio
async def should_set_rls_context_with_empty_roles_when_no_roles():
    """set_rls_context doit gérer le cas où l'utilisateur n'a pas de rôles."""
    mock_session = AsyncMock()
    await set_rls_context(mock_session, "user-uuid-456", "")
    assert mock_session.execute.call_count == 2
    second_call = mock_session.execute.call_args_list[1]
    assert second_call.args[1]["roles"] == ""


@pytest.mark.asyncio
async def should_inject_rls_context_when_get_db_rls_yields_session():
    """get_db_rls doit injecter le contexte RLS avant de fournir la session."""
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=AsyncMock())
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_ctx)

    import gsie_api.infrastructure.database as db_module

    original_factory = db_module.async_session_factory
    db_module.async_session_factory = mock_factory

    try:
        user = {"sub": "user-uuid-789", "roles": ["admin", "dpo"]}
        gen = get_db_rls(user=user)
        session = await gen.__anext__()
        # set_rls_context doit avoir été appelé (2 execute)
        assert mock_session.execute.call_count == 2
        # Vérifier que l'user_id et les rôles sont bien injectés
        first_call = mock_session.execute.call_args_list[0]
        assert first_call.args[1]["uid"] == "user-uuid-789"
        second_call = mock_session.execute.call_args_list[1]
        assert second_call.args[1]["roles"] == "admin,dpo"
        assert session is mock_session
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()
    finally:
        db_module.async_session_factory = original_factory


@pytest.mark.asyncio
async def should_use_empty_string_when_sub_missing_in_get_db_rls():
    """get_db_rls doit gérer l'absence de 'sub' dans le payload JWT."""
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=AsyncMock())
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_ctx)

    import gsie_api.infrastructure.database as db_module

    original_factory = db_module.async_session_factory
    db_module.async_session_factory = mock_factory

    try:
        user = {}  # Pas de sub, pas de roles
        gen = get_db_rls(user=user)
        await gen.__anext__()
        first_call = mock_session.execute.call_args_list[0]
        assert first_call.args[1]["uid"] == ""
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()
    finally:
        db_module.async_session_factory = original_factory


# ─────────────────────────────────────────────────────────────────────────
# set_rls_context — branche SQLite et workspace/organisation Postgres
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def should_store_context_in_session_info_when_sqlite_dialect():
    """set_rls_context doit contourner SET LOCAL (indisponible) en SQLite."""
    mock_session = AsyncMock()
    mock_session.bind = MagicMock()
    mock_session.bind.dialect.name = "sqlite"
    mock_session.info = {}

    await set_rls_context(
        mock_session,
        "user-1",
        "admin",
        workspace_id="ws-1",
        organisation_id="org-1",
    )

    mock_session.execute.assert_not_called()
    assert mock_session.info["user_id"] == "user-1"
    assert mock_session.info["roles"] == "admin"
    assert mock_session.info["organisation_id"] == "org-1"
    assert mock_session.info["workspace_id"] == "ws-1"


@pytest.mark.asyncio
async def should_treat_missing_bind_as_non_sqlite():
    """Sans bind (session non liée à un engine), la branche SQLite est ignorée."""
    mock_session = AsyncMock()
    mock_session.bind = None
    mock_session.info = {}

    await set_rls_context(mock_session, "user-1", "")

    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def should_set_workspace_config_when_workspace_id_given():
    mock_session = AsyncMock()
    mock_session.bind = MagicMock()
    mock_session.bind.dialect.name = "postgresql"
    mock_session.info = {}

    await set_rls_context(mock_session, "user-1", "admin", workspace_id="ws-42")

    assert mock_session.execute.call_count == 3
    third_call = mock_session.execute.call_args_list[2]
    assert "app.current_workspace_id" in third_call.args[0].text
    assert third_call.args[1]["wid"] == "ws-42"
    assert mock_session.info["workspace_id"] == "ws-42"


@pytest.mark.asyncio
async def should_set_organisation_config_when_organisation_id_given():
    mock_session = AsyncMock()
    mock_session.bind = MagicMock()
    mock_session.bind.dialect.name = "postgresql"
    mock_session.info = {}

    await set_rls_context(mock_session, "user-1", "admin", organisation_id="org-42")

    assert mock_session.execute.call_count == 3
    third_call = mock_session.execute.call_args_list[2]
    assert "app.current_organisation_id" in third_call.args[0].text
    assert third_call.args[1]["oid"] == "org-42"
    assert mock_session.info["organisation_id"] == "org-42"


# ─────────────────────────────────────────────────────────────────────────
# _resolve_active_organisation
# ─────────────────────────────────────────────────────────────────────────


class _FakeHeaders(dict):
    def get(self, key, default=None):  # noqa: D102 - dict.get override intentionnel
        return super().get(key, default)


class _FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = _FakeHeaders(headers or {})


class TestResolveActiveOrganisation:
    _USER_ID = str(uuid4())

    @pytest.mark.asyncio
    async def should_raise_400_when_header_is_not_a_uuid(self) -> None:
        session = AsyncMock()
        request = _FakeRequest({"X-Organisation-Id": "not-a-uuid"})

        with pytest.raises(HTTPException) as captured:
            await _resolve_active_organisation(session, self._USER_ID, request)

        assert captured.value.status_code == 400

    @pytest.mark.asyncio
    async def should_raise_403_when_header_valid_but_not_member(self) -> None:
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=None)
        org_id = uuid4()
        request = _FakeRequest({"X-Organisation-Id": str(org_id)})

        with pytest.raises(HTTPException) as captured:
            await _resolve_active_organisation(session, self._USER_ID, request)

        assert captured.value.status_code == 403

    @pytest.mark.asyncio
    async def should_return_organisation_id_when_header_valid_and_member(self) -> None:
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=1)
        org_id = uuid4()
        request = _FakeRequest({"X-Organisation-Id": str(org_id)})

        result = await _resolve_active_organisation(session, self._USER_ID, request)

        assert result == str(org_id)

    @pytest.mark.asyncio
    async def should_raise_409_when_no_header_and_multiple_organisations(self) -> None:
        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = [uuid4(), uuid4()]
        session.execute = AsyncMock(return_value=execute_result)
        request = _FakeRequest()

        with pytest.raises(HTTPException) as captured:
            await _resolve_active_organisation(session, self._USER_ID, request)

        assert captured.value.status_code == 409

    @pytest.mark.asyncio
    async def should_return_none_when_no_header_and_no_organisation(self) -> None:
        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=execute_result)
        request = _FakeRequest()

        result = await _resolve_active_organisation(session, self._USER_ID, request)

        assert result is None

    @pytest.mark.asyncio
    async def should_return_sole_organisation_when_no_header_and_single_match(self) -> None:
        session = AsyncMock()
        org_id = uuid4()
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = [org_id]
        session.execute = AsyncMock(return_value=execute_result)
        request = _FakeRequest()

        result = await _resolve_active_organisation(session, self._USER_ID, request)

        assert result == str(org_id)

    @pytest.mark.asyncio
    async def should_return_none_when_user_id_is_not_a_uuid_and_no_header(self) -> None:
        """Un user_id non-UUID (ex. token de test) ne peut avoir d'organisation
        en base — on évite la requête SQL qui échouerait sur le cast UUID."""
        session = AsyncMock()
        request = _FakeRequest()

        result = await _resolve_active_organisation(session, "non-uuid-subject", request)

        assert result is None
        session.execute.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────
# _resolve_active_workspace
# ─────────────────────────────────────────────────────────────────────────


class TestResolveActiveWorkspace:
    @pytest.mark.asyncio
    async def should_return_none_when_no_candidate(self) -> None:
        session = AsyncMock()
        request = _FakeRequest()

        result = await _resolve_active_workspace(session, str(uuid4()), request, None)

        assert result is None
        session.scalar.assert_not_called()

    @pytest.mark.asyncio
    async def should_return_none_when_no_organisation_id(self) -> None:
        session = AsyncMock()
        request = _FakeRequest({"X-Workspace-Id": str(uuid4())})

        result = await _resolve_active_workspace(session, None, request, None)

        assert result is None

    @pytest.mark.asyncio
    async def should_raise_400_when_candidate_is_not_a_uuid(self) -> None:
        session = AsyncMock()
        request = _FakeRequest({"X-Workspace-Id": "not-a-uuid"})

        with pytest.raises(HTTPException) as captured:
            await _resolve_active_workspace(session, str(uuid4()), request, None)

        assert captured.value.status_code == 400

    @pytest.mark.asyncio
    async def should_raise_403_when_workspace_not_found_in_organisation(self) -> None:
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=None)
        request = _FakeRequest({"X-Workspace-Id": str(uuid4())})

        with pytest.raises(HTTPException) as captured:
            await _resolve_active_workspace(session, str(uuid4()), request, None)

        assert captured.value.status_code == 403

    @pytest.mark.asyncio
    async def should_return_workspace_id_when_found(self) -> None:
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=1)
        ws_id = uuid4()
        request = _FakeRequest({"X-Workspace-Id": str(ws_id)})

        result = await _resolve_active_workspace(session, str(uuid4()), request, None)

        assert result == str(ws_id)

    @pytest.mark.asyncio
    async def should_fallback_to_token_workspace_id_when_no_header(self) -> None:
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=1)
        ws_id = uuid4()
        request = _FakeRequest()

        result = await _resolve_active_workspace(session, str(uuid4()), request, ws_id)

        assert result == str(ws_id)


# ─────────────────────────────────────────────────────────────────────────
# get_db_user_rls
# ─────────────────────────────────────────────────────────────────────────


class TestGetDbUserRls:
    @pytest.mark.asyncio
    async def should_inject_workspace_id_when_present_in_token(self) -> None:
        mock_session = AsyncMock()
        mock_session.begin = MagicMock(return_value=AsyncMock())
        mock_session.bind = None
        mock_session.info = {}
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_factory = MagicMock(return_value=mock_ctx)

        import gsie_api.infrastructure.database as db_module

        original_factory = db_module.async_session_factory
        db_module.async_session_factory = mock_factory

        try:
            ws_id = uuid4()
            user = {"sub": "user-1", "roles": ["admin"], "workspace_id": ws_id}
            gen = get_db_user_rls(user=user)
            session = await gen.__anext__()
            assert session is mock_session
            with contextlib.suppress(StopAsyncIteration):
                await gen.__anext__()
        finally:
            db_module.async_session_factory = original_factory

    @pytest.mark.asyncio
    async def should_omit_workspace_id_when_absent_from_token(self) -> None:
        mock_session = AsyncMock()
        mock_session.begin = MagicMock(return_value=AsyncMock())
        mock_session.bind = None
        mock_session.info = {}
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_factory = MagicMock(return_value=mock_ctx)

        import gsie_api.infrastructure.database as db_module

        original_factory = db_module.async_session_factory
        db_module.async_session_factory = mock_factory

        try:
            user = {"sub": "user-1", "roles": []}
            gen = get_db_user_rls(user=user)
            await gen.__anext__()
            with contextlib.suppress(StopAsyncIteration):
                await gen.__anext__()
        finally:
            db_module.async_session_factory = original_factory


# ─────────────────────────────────────────────────────────────────────────
# get_db_resource
# ─────────────────────────────────────────────────────────────────────────


class TestGetDbResource:
    @pytest.mark.asyncio
    async def should_use_headers_directly_when_not_postgresql(self) -> None:
        session = AsyncMock()
        session.bind = MagicMock()
        session.bind.dialect.name = "sqlite"
        session.info = {}
        org_id = uuid4()
        ws_id = uuid4()
        request = _FakeRequest({"X-Organisation-Id": str(org_id), "X-Workspace-Id": str(ws_id)})
        user = {"sub": "user-1", "roles": ["admin"]}

        gen = get_db_resource(request, user, session)
        result_session = await gen.__anext__()

        assert result_session is session
        assert session.info["organisation_id"] == str(org_id)
        assert session.info["workspace_id"] == str(ws_id)
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()

    @pytest.mark.asyncio
    async def should_fallback_to_token_workspace_when_no_header_and_not_postgresql(
        self,
    ) -> None:
        session = AsyncMock()
        session.bind = MagicMock()
        session.bind.dialect.name = "sqlite"
        session.info = {}
        ws_id = uuid4()
        org_id = uuid4()
        request = _FakeRequest({"X-Organisation-Id": str(org_id)})
        user = {"sub": "user-1", "roles": [], "workspace_id": ws_id}

        gen = get_db_resource(request, user, session)
        await gen.__anext__()

        assert session.info["organisation_id"] == str(org_id)
        assert session.info["workspace_id"] == str(ws_id)
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()

    @pytest.mark.asyncio
    async def should_not_set_organisation_context_twice_when_none_resolved(self) -> None:
        session = AsyncMock()
        session.bind = MagicMock()
        # Ni "postgresql" (résolution via requêtes) ni "sqlite" (info dict) —
        # exerce la branche SET LOCAL générique de set_rls_context sans
        # organisation_id ni workspace_id résolus depuis les en-têtes.
        session.bind.dialect.name = "mysql"
        session.info = {}
        request = _FakeRequest()
        user = {"sub": "user-1", "roles": []}

        gen = get_db_resource(request, user, session)
        await gen.__anext__()

        # set_rls_context appelé une seule fois (pas de organisation_id résolu).
        assert session.execute.call_count == 2
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()

    @pytest.mark.asyncio
    async def should_resolve_organisation_and_workspace_via_postgresql_queries(
        self,
    ) -> None:
        session = AsyncMock()
        session.bind = MagicMock()
        session.bind.dialect.name = "postgresql"
        session.info = {}
        org_id = uuid4()
        ws_id = uuid4()
        # scalar() sert aux vérifications d'appartenance (organisation puis workspace).
        session.scalar = AsyncMock(return_value=1)
        request = _FakeRequest({"X-Organisation-Id": str(org_id), "X-Workspace-Id": str(ws_id)})
        user = {"sub": "user-1", "roles": ["admin"]}

        gen = get_db_resource(request, user, session)
        result_session = await gen.__anext__()

        assert result_session is session
        assert session.info["organisation_id"] == str(org_id)
        assert session.info["workspace_id"] == str(ws_id)
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()
