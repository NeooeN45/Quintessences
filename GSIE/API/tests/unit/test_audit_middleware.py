"""Tests unitaires — AuditMiddleware (capture des mutations HTTP).

Le middleware est fire-and-forget : une erreur d'audit ne doit jamais
casser la requête principale. Ces tests couvrent :
- l'exclusion des GET et des routes techniques,
- la capture des méthodes de mutation (POST/PUT/PATCH/DELETE),
- l'extraction de l'IP via ``core.limiter.get_client_address`` (pentest
  du 2026-08-07),
- l'extraction de l'acteur et de la ressource,
- la déduction de l'action,
- la tolérance aux erreurs d'audit (fire-and-forget).

Conventions (AGENTS.md API) : pytest-asyncio mode ``auto``, nommage
``should_[expected]_when_[condition]``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from gsie_api.audit.middleware import (
    AuditMiddleware,
    _deduce_action,
    _extract_actor,
    _extract_resource,
)
from gsie_api.audit.service import AuditEntry  # noqa: TC001

# ─────────────────────────────────────────────────────────────────────────
# Application Starlette minimale montant le middleware
# ─────────────────────────────────────────────────────────────────────────


async def _endpoint_ok(request):
    del request
    return JSONResponse({"ok": True}, status_code=201)


async def _endpoint_with_user(request):
    request.state.user = {"sub": str(uuid4()), "email": "forestier@example.com"}
    return JSONResponse({"ok": True}, status_code=200)


async def _endpoint_with_trace(request):
    request.state.trace_id = "trace-abc-123"
    return JSONResponse({"ok": True}, status_code=200)


async def _health_endpoint(request):
    del request
    return PlainTextResponse("ok")


def _build_client(audit_service: AsyncMock) -> TestClient:
    routes = [
        Route("/api/v1/resources/{resource_id}", _endpoint_ok, methods=["POST", "GET"]),
        Route("/api/v1/resources/{resource_id}", _endpoint_ok, methods=["PUT", "PATCH", "DELETE"]),
        Route("/api/v1/auth/login", _endpoint_ok, methods=["POST"]),
        Route("/api/v1/orgs/{org_id}/members", _endpoint_ok, methods=["POST", "DELETE"]),
        Route("/api/v1/sync/geosylva/parcelles/{cid}", _endpoint_ok, methods=["PUT"]),
        Route("/api/v1/with-user", _endpoint_with_user, methods=["POST"]),
        Route("/api/v1/with-trace", _endpoint_with_trace, methods=["POST"]),
        Route("/health", _health_endpoint, methods=["GET", "POST"]),
    ]
    app = Starlette(
        routes=routes,
        middleware=[Middleware(AuditMiddleware, audit_service=audit_service)],
    )
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────
# dispatch() — exclusions et capture
# ─────────────────────────────────────────────────────────────────────────


class TestDispatchExclusions:
    def should_not_audit_get_requests_by_default(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        response = client.get("/api/v1/resources/res-1")

        assert response.status_code == 201
        service.log.assert_not_called()

    def should_not_audit_excluded_technical_routes(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        response = client.post("/health")

        assert response.status_code == 200
        service.log.assert_not_called()


class TestDispatchMutationCapture:
    def should_audit_post_request(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        response = client.post("/api/v1/resources/res-1")

        assert response.status_code == 201
        service.log.assert_awaited_once()
        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.method == "POST"
        assert entry.status_code == 201
        assert entry.action == "create"

    def should_audit_put_request(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        response = client.put("/api/v1/resources/res-1")

        assert response.status_code == 201
        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.method == "PUT"
        assert entry.action == "update"

    def should_audit_patch_request(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        response = client.patch("/api/v1/resources/res-1")

        assert response.status_code == 201
        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.action == "update"

    def should_audit_delete_request(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        response = client.delete("/api/v1/resources/res-1")

        assert response.status_code == 201
        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.method == "DELETE"
        assert entry.action == "delete"

    def should_extract_client_ip_via_get_client_address(self) -> None:
        """Le middleware délègue l'extraction d'IP à core.limiter.get_client_address
        (remplacement de l'extraction ad-hoc lors du pentest du 2026-08-07)."""
        service = AsyncMock()
        client = _build_client(service)

        client.post("/api/v1/resources/res-1")

        entry: AuditEntry = service.log.await_args.args[0]
        # TestClient envoie ses requêtes depuis testclient — get_remote_address
        # doit avoir produit une IP non vide (fallback de get_client_address).
        assert entry.ip_address

    def should_capture_trace_id_when_present(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        client.post("/api/v1/with-trace")

        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.trace_id == "trace-abc-123"

    def should_use_none_trace_id_when_absent(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        client.post("/api/v1/resources/res-1")

        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.trace_id is None

    def should_capture_actor_when_authenticated(self) -> None:
        service = AsyncMock()
        client = _build_client(service)

        client.post("/api/v1/with-user")

        entry: AuditEntry = service.log.await_args.args[0]
        assert entry.actor_id is not None
        assert entry.actor_email == "forestier@example.com"


class TestDispatchFireAndForget:
    async def should_not_break_request_when_audit_service_raises(self) -> None:
        service = AsyncMock()
        service.log.side_effect = RuntimeError("DB indisponible")
        client = _build_client(service)

        response = client.post("/api/v1/resources/res-1")

        # La requête principale aboutit malgré l'échec de l'audit.
        assert response.status_code == 201
        service.log.assert_awaited_once()


# ─────────────────────────────────────────────────────────────────────────
# _extract_actor
# ─────────────────────────────────────────────────────────────────────────


class TestExtractActor:
    def should_return_none_none_when_no_user_in_state(self) -> None:
        request = _fake_request_with_state()
        actor_id, actor_email = _extract_actor(request)
        assert actor_id is None
        assert actor_email is None

    def should_return_actor_when_user_has_valid_sub(self) -> None:
        uid = uuid4()
        request = _fake_request_with_state(user={"sub": str(uid), "email": "a@b.fr"})
        actor_id, actor_email = _extract_actor(request)
        assert actor_id == uid
        assert actor_email == "a@b.fr"

    def should_return_none_id_when_sub_is_invalid_uuid(self) -> None:
        request = _fake_request_with_state(user={"sub": "not-a-uuid", "email": "a@b.fr"})
        actor_id, actor_email = _extract_actor(request)
        assert actor_id is None
        assert actor_email == "a@b.fr"

    def should_return_none_email_when_user_not_a_dict(self) -> None:
        class FakeUser:
            def get(self, key, default=None):
                return str(uuid4()) if key == "sub" else default

        request = _fake_request_with_state(user=FakeUser())
        actor_id, actor_email = _extract_actor(request)
        assert actor_id is not None
        assert actor_email is None


class _FakeState:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class _FakeRequest:
    def __init__(self, state: _FakeState, path: str = "/api/v1/resources/res-1") -> None:
        self.state = state

        class _URL:
            def __init__(self, p: str) -> None:
                self.path = p

        self.url = _URL(path)


def _fake_request_with_state(path: str = "/api/v1/resources/res-1", **state_kwargs) -> _FakeRequest:
    return _FakeRequest(_FakeState(**state_kwargs), path=path)


# ─────────────────────────────────────────────────────────────────────────
# _extract_resource
# ─────────────────────────────────────────────────────────────────────────


class TestExtractResource:
    def should_return_unknown_when_path_is_root(self) -> None:
        request = _fake_request_with_state(path="/")
        resource_type, resource_id = _extract_resource(request)
        assert resource_type == "unknown"
        assert resource_id is None

    def should_strip_api_version_prefix(self) -> None:
        request = _fake_request_with_state(path="/api/v1/resources/res-42")
        resource_type, resource_id = _extract_resource(request)
        assert resource_type == "resources"
        assert resource_id == "res-42"

    def should_return_unknown_when_only_api_version_prefix(self) -> None:
        request = _fake_request_with_state(path="/api/v1")
        resource_type, resource_id = _extract_resource(request)
        assert resource_type == "unknown"
        assert resource_id is None

    def should_return_none_resource_id_when_single_segment(self) -> None:
        request = _fake_request_with_state(path="/api/v1/resources")
        resource_type, resource_id = _extract_resource(request)
        assert resource_type == "resources"
        assert resource_id is None

    def should_not_strip_prefix_when_not_api_version(self) -> None:
        request = _fake_request_with_state(path="/gis/status")
        resource_type, resource_id = _extract_resource(request)
        assert resource_type == "gis"
        assert resource_id == "status"


# ─────────────────────────────────────────────────────────────────────────
# _deduce_action
# ─────────────────────────────────────────────────────────────────────────


class TestDeduceAction:
    def should_return_login_for_auth_login_path(self) -> None:
        assert _deduce_action("POST", "/api/v1/auth/login") == "login"

    def should_return_logout_for_auth_logout_path(self) -> None:
        assert _deduce_action("POST", "/api/v1/auth/logout") == "logout"

    def should_return_invite_for_members_post(self) -> None:
        assert _deduce_action("POST", "/api/v1/orgs/org-1/members") == "invite"

    def should_return_revoke_for_members_delete(self) -> None:
        assert _deduce_action("DELETE", "/api/v1/orgs/org-1/members") == "revoke"

    def should_return_sync_for_sync_path(self) -> None:
        assert _deduce_action("PUT", "/api/v1/sync/geosylva/parcelles/p1") == "sync"

    def should_return_create_for_generic_post(self) -> None:
        assert _deduce_action("POST", "/api/v1/resources") == "create"

    def should_return_update_for_put(self) -> None:
        assert _deduce_action("PUT", "/api/v1/resources/res-1") == "update"

    def should_return_update_for_patch(self) -> None:
        assert _deduce_action("PATCH", "/api/v1/resources/res-1") == "update"

    def should_return_delete_for_generic_delete(self) -> None:
        assert _deduce_action("DELETE", "/api/v1/resources/res-1") == "delete"

    def should_return_export_for_export_path_on_non_mutation_method(self) -> None:
        # Uniquement atteignable hors des méthodes de mutation captées par le
        # middleware (branche défensive de la fonction pure) — appel direct.
        assert _deduce_action("GET", "/api/v1/resources/export") == "export"

    def should_return_read_as_default_fallback(self) -> None:
        assert _deduce_action("GET", "/api/v1/resources/res-1") == "read"
