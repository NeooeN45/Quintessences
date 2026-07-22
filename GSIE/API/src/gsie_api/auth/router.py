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
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from gsie_api.auth.refresh_tokens import RefreshTokenStore, get_refresh_token_store
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

from gsie_api.core.limiter import limiter as _limiter  # noqa: E402

router = APIRouter(prefix="/auth", tags=["auth"])

# UUID fixe pour l'utilisateur de développement (stub — DB en Phase 4 semaine 3).
# BUG CORRIGÉ : le JWT émettait auparavant `sub=credentials.username` (ex.
# "admin"), une chaîne non-UUID. `resources/router.py::_extract_author_id`
# attend un UUID et échoue silencieusement (except ValueError -> None) sur
# "admin", donc `author_id` restait NULL sur toute Revision créée via le
# CRUD générique — traçabilité d'auteur cassée (CON-010/CON-005). Le
# `subject` du token est maintenant ce UUID fixe ; `credentials.username`
# reste utilisé uniquement pour la vérification des identifiants de login.
DEV_USER_ID = "00000000-0000-0000-0000-000000000001"


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
    # Comparaison directe en dev (le password de config n'est pas hashé)
    # En production, les utilisateurs seront en DB avec un hash bcrypt.
    if password != _settings.auth_dev_password:
        return None
    # Générer un hash pour le token (pas pour la vérification)
    password_hash = bcrypt.hashpw(
        _settings.auth_dev_password.encode("utf-8"),
        bcrypt.gensalt(),
    )
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
@_limiter.limit("20/minute")
async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
) -> TokenResponse:
    """Authentifie un utilisateur de développement et retourne les tokens JWT."""
    if not _settings.auth_dev_login_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    # Audit — IP et User-Agent pour traçabilité (CON-005, OWASP A09)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    user = _authenticate_user(credentials.username, credentials.password)
    if user is None:
        logger.warning(
            "login_failed",
            username=credentials.username,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_claims: dict[str, object] = {
        "roles": user["roles"],
        "username": credentials.username,
    }
    access_token = create_access_token(
        subject=DEV_USER_ID,
        claims=session_claims,
    )
    refresh_token = create_refresh_token(
        subject=DEV_USER_ID,
        claims=session_claims,
    )
    refresh_payload = verify_token(refresh_token, expected_type="refresh")
    await refresh_store.register(
        str(refresh_payload["jti"]),
        float(refresh_payload["exp"]),
    )

    logger.info(
        "login_success",
        username=credentials.username,
        client_ip=client_ip,
        user_agent=user_agent,
    )

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
async def refresh_token(
    request: RefreshRequest,
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
) -> TokenResponse:
    """Échange un refresh token contre un nouveau access token."""
    payload = verify_token(request.refresh_token, expected_type="refresh")
    subject = payload.get("sub")
    jti = payload.get("jti")
    if not isinstance(subject, str) or not isinstance(jti, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims",
        )

    roles_claim = payload.get("roles", [])
    if isinstance(roles_claim, str):
        roles = [roles_claim]
    elif isinstance(roles_claim, list):
        roles = [role for role in roles_claim if isinstance(role, str)]
    else:
        roles = []
    session_claims: dict[str, object] = {"roles": roles}
    username = payload.get("username")
    if isinstance(username, str):
        session_claims["username"] = username

    access_token = create_access_token(subject=subject, claims=session_claims)
    new_refresh_token = create_refresh_token(subject=subject, claims=session_claims)
    new_payload = verify_token(new_refresh_token, expected_type="refresh")
    rotated = await refresh_store.rotate(
        jti,
        str(new_payload["jti"]),
        float(new_payload["exp"]),
    )
    if not rotated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or already used",
        )

    logger.info("token_refreshed", username=username or subject, jti=jti)

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
