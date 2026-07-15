"""Tests unitaires — middleware (shared/middleware.py)."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from gsie_api.shared.middleware import TraceIdMiddleware, _validate_trace_id


def should_return_none_when_trace_id_is_none():
    """_validate_trace_id doit retourner None si pas de trace_id."""
    assert _validate_trace_id(None) is None


def should_return_trace_id_when_valid():
    """_validate_trace_id doit retourner la valeur si valide."""
    assert _validate_trace_id("my-trace-123") == "my-trace-123"


def should_return_none_when_trace_id_contains_script():
    """_validate_trace_id doit retourner None si invalide (XSS)."""
    assert _validate_trace_id("<script>alert(1)</script>") is None


def should_return_none_when_trace_id_too_long():
    """_validate_trace_id doit retourner None si > 64 caractères."""
    assert _validate_trace_id("a" * 65) is None


def should_return_none_when_trace_id_has_spaces():
    """_validate_trace_id doit retourner None si contient des espaces."""
    assert _validate_trace_id("trace id 123") is None


def should_accept_trace_id_with_64_chars():
    """_validate_trace_id doit accepter exactement 64 caractères."""
    valid = "a" * 64
    assert _validate_trace_id(valid) == valid


def should_remove_server_header_when_present():
    """Le middleware doit supprimer le header Server s'il est présent."""
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        # La route ajoute volontairement un header server
        response = JSONResponse({"ok": True})
        response.headers["server"] = "test-server"
        return response

    client = TestClient(app)
    response = client.get("/test")
    assert "server" not in {k.lower() for k in response.headers}


def should_return_413_when_content_length_exceeds_limit():
    """Le middleware doit retourner 413 si content-length > limite."""
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get(
        "/test",
        headers={"content-length": str(10 * 1024 * 1024)},  # 10 MiB
    )
    assert response.status_code == 413


def should_return_400_when_content_length_non_numeric():
    """Le middleware doit retourner 400 si content-length non numérique.

    Évite le crash ValueError sur int("abc") (P0 résilience).
    """
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test", headers={"content-length": "abc"})
    assert response.status_code == 400
    assert response.json()["error_code"] == "BAD_REQUEST"


def should_return_413_when_content_length_negative():
    """Le middleware doit retourner 413 si content-length négatif.

    Évite le crash ou comportement inattendu sur int("-1") (P0 résilience).
    """
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test", headers={"content-length": "-1"})
    assert response.status_code == 413
