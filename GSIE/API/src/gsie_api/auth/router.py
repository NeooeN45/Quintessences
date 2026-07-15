"""Router auth — endpoints login, refresh, verify (DEC-000019).

Endpoints :
- POST /auth/login : authentifie un utilisateur et retourne access + refresh tokens
- POST /auth/refresh : échange un refresh token contre un nouveau access token
- GET /auth/verify : vérifie la validité d'un access token

Note : le modèle utilisateur (DB) sera implémenté en Phase 4 semaine 3.
En attendant, un stub utilisateur est utilisé pour les tests.
"""

from datetime import UTC
from typing import Annotated, TypedDict

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status

from gsie_api.auth.schemas import LoginRequest, RefreshRequest, TokenResponse, VerifyResponse
from gsie_api.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_token,
)
from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger

_settings = get_settings()
logger = get_logger("gsie_api.auth.router")

router = APIRouter(prefix="/auth", tags=["auth"])

class DevUser(TypedDict):
    """Utilisateur local strictement réservé au développement."""

    password_hash: bytes
    roles: list[str]


def _get_dev_user(username: str, password: str) -> DevUser | None:
    """Authentifie un utilisateur de développement via env vars.

    Returns:
        Dict utilisateur si authentifié, None sinon.
    """
    if not _settings.auth_dev_login_enabled:
        return None
    if not _settings.auth_dev_username or not _settings.auth_dev_password:
        return None
    if username != _settings.auth_dev_username:
        return None
    password_hash = bcrypt.hashpw(
        _settings.auth_dev_password.encode("utf-8"),
        bcrypt.gensalt(),
    )
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
        return None
    return DevUser(password_hash=password_hash, roles=["admin"])


def _authenticate_user(username: str, password: str) -> DevUser | None:
    """Authentifie un utilisateur (stub — DB en Phase 4 semaine 3).

    Returns:
        Dict utilisateur si authentifié, None sinon.
    """
    return _get_dev_user(username, password)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authentifier un utilisateur",
    description=(
        "Authentifie un utilisateur avec username + password et retourne "
        "un access token (15 min) et un refresh token (7 jours). "
        "Les tokens sont signés en RS256 (DEC-000019)."
    ),
)
async def login(credentials: LoginRequest) -> TokenResponse:
    """Authentifie un utilisateur de développement et retourne les tokens JWT."""
    if not _settings.auth_dev_login_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    user = _authenticate_user(credentials.username, credentials.password)
    if user is None:
        logger.warning("login_failed", username=credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=credentials.username,
        claims={"roles": user["roles"]},
    )
    refresh_token = create_refresh_token(subject=credentials.username)

    logger.info("login_success", username=credentials.username)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rafraîchir le token d'accès",
    description=(
        "Échange un refresh token valide contre un nouveau access token "
        "et un nouveau refresh token (rotation)."
    ),
)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """Échange un refresh token contre un nouveau access token."""
    payload = verify_token(request.refresh_token, expected_type="refresh")
    username = payload["sub"]

    access_token = create_access_token(subject=username)
    new_refresh_token = create_refresh_token(subject=username)

    logger.info("token_refreshed", username=username)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.get(
    "/verify",
    response_model=VerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Vérifier un token",
    description="Vérifie la validité du token d'accès fourni dans le header Authorization.",
)
async def verify_access_token(
    user: Annotated[dict[str, object], Depends(get_current_user)],
) -> VerifyResponse:
    """Vérifie la validité du token d'accès."""
    from datetime import datetime as dt

    exp = user.get("exp")
    expires_at = dt.fromtimestamp(exp, tz=UTC).isoformat() if isinstance(exp, int | float) else None
    subject = user.get("sub")
    token_type = user.get("type")

    return VerifyResponse(
        valid=True,
        subject=subject if isinstance(subject, str) else None,
        token_type=token_type if isinstance(token_type, str) else None,
        expires_at=expires_at,
    )
