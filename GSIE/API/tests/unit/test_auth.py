"""Tests unitaires — authentification JWT RS256 (auth/router.py + core/auth.py)."""

from fastapi.testclient import TestClient

from gsie_api.app import create_app

client = TestClient(create_app())


def should_return_200_and_tokens_when_login_valid():
    """POST /auth/login doit retourner access + refresh tokens pour credentials valides."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] > 0


def should_return_401_when_login_invalid():
    """POST /auth/login doit retourner 401 pour credentials invalides."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert response.status_code == 401


def should_return_401_when_login_unknown_user():
    """POST /auth/login doit retourner 401 pour un utilisateur inexistant."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "unknown", "password": "anything"},
    )
    assert response.status_code == 401


def should_return_200_and_new_tokens_when_refresh_valid():
    """POST /auth/refresh doit retourner de nouveaux tokens pour un refresh valide."""
    # D'abord login pour obtenir un refresh token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Puis refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def should_return_401_when_refresh_with_access_token():
    """POST /auth/refresh doit refuser un access token (mauvais type)."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme"},
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401


def should_return_200_when_verify_with_valid_token():
    """GET /auth/verify doit retourner valid=True pour un token valide."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["subject"] == "admin"
    assert data["token_type"] == "access"


def should_return_401_when_verify_without_token():
    """GET /auth/verify doit retourner 401 sans token."""
    response = client.get("/api/v1/auth/verify")
    assert response.status_code == 401


def should_return_401_when_verify_with_invalid_token():
    """GET /auth/verify doit retourner 401 pour un token invalide."""
    response = client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": "Bearer invalid-token-string"},
    )
    assert response.status_code == 401


def should_create_and_verify_access_token():
    """create_access_token + verify_token doivent fonctionner ensemble."""
    from gsie_api.core.auth import create_access_token, verify_token

    token = create_access_token(subject="test-user", claims={"role": "admin"})
    payload = verify_token(token, expected_type="access")
    assert payload["sub"] == "test-user"
    assert payload["type"] == "access"
    assert payload["role"] == "admin"


def should_create_and_verify_refresh_token():
    """create_refresh_token + verify_token doivent fonctionner ensemble."""
    from gsie_api.core.auth import create_refresh_token, verify_token

    token = create_refresh_token(subject="test-user")
    payload = verify_token(token, expected_type="refresh")
    assert payload["sub"] == "test-user"
    assert payload["type"] == "refresh"


def should_reject_expired_token():
    """verify_token doit rejeter un token expiré."""
    from datetime import timedelta
    from unittest.mock import patch

    import jwt
    from gsie_api.core.auth import _load_private_key, verify_token
    from gsie_api.core.config import get_settings

    settings = get_settings()
    # Créer un token déjà expiré
    from datetime import UTC, datetime

    payload = {
        "sub": "test",
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "type": "access",
    }
    expired_token = jwt.encode(payload, _load_private_key(), algorithm=settings.jwt_algorithm)

    from fastapi import HTTPException

    try:
        verify_token(expired_token, expected_type="access")
        assert False, "Should have raised HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert "expired" in exc.detail.lower()
