"""Router auth — endpoints login, refresh, verify (DEC-000019).

Endpoints :
- POST /auth/login : authentifie un utilisateur et retourne access + refresh tokens
- POST /auth/refresh : échange un refresh token contre un nouveau access token
- GET /auth/verify : vérifie la validité d'un access token

Note : le modèle utilisateur (DB) sera implémenté en Phase 4 semaine 3.
En attendant, un stub utilisateur est utilisé pour les tests.
"""

from datetime import UTC, datetime, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status

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

# Stub utilisateur — remplacé par DB en Phase 4 semaine 3
# Format : { "username": { "password_hash": bytes, "roles": ["admin"] } }
_DEV_USERS: dict[str, dict] = {
    "admin": {
        "password_hash": bcrypt.hashpw(b"changeme", bcrypt.gensalt()),
        "roles": ["admin"],
    },
}


def _authenticate_user(username: str, password: str) -> dict | None:
    """Authentifie un utilisateur (stub — DB en Phase 4 semaine 3).

    Returns:
        Dict utilisateur si authentifié, None sinon.
    """
    user = _DEV_USERS.get(username)
    if user is None:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
        return None
    return user


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
    """Authentifie un utilisateur et retourne les tokens JWT."""
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
    user: dict = Depends(get_current_user),
) -> VerifyResponse:
    """Vérifie la validité du token d'accès."""
    from datetime import datetime as dt

    exp = user.get("exp")
    expires_at = dt.fromtimestamp(exp, tz=UTC).isoformat() if exp else None

    return VerifyResponse(
        valid=True,
        subject=user.get("sub"),
        token_type=user.get("type"),
        expires_at=expires_at,
    )
