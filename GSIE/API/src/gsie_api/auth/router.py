"""Router auth — endpoints login, refresh, verify (DEC-000019).

Endpoints :
- POST /auth/login : authentifie un utilisateur et retourne access + refresh tokens
- POST /auth/refresh : échange un refresh token contre un nouveau access token
- GET /auth/verify : vérifie la validité d'un access token

Note : le modèle utilisateur (DB) sera implémenté en Phase 4 semaine 3.
En attendant, un stub utilisateur est utilisé pour les tests.
"""

import hmac
from collections.abc import Awaitable, Callable
from datetime import UTC
from typing import Annotated, TypedDict
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.auth.refresh_tokens import RefreshTokenStore, get_refresh_token_store
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from gsie_api.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    TokenResponse,
    TurnstileVerifyRequest,
    VerifyResponse,
)
from gsie_api.auth.sessions import SessionService, SqlAlchemySessionRepository
from gsie_api.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_token,
)
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import get_client_address
from gsie_api.core.logging import get_logger
from gsie_api.infrastructure import database as database_infrastructure
from gsie_api.infrastructure.database import get_db
from gsie_api.shared.turnstile import TurnstileClient

_settings = get_settings()


async def get_session_service(session: Annotated[AsyncSession, Depends(get_db)]) -> SessionService:
    """Dependency du suivi des sessions pendant la rotation des tokens."""
    return SessionService(SqlAlchemySessionRepository(session))


logger = get_logger("gsie_api.auth.router")

from gsie_api.core.limiter import limiter as _limiter  # noqa: E402

router = APIRouter(prefix="/auth", tags=["auth"])


async def _revoke_account_sessions(
    subject: str,
    refresh_store: RefreshTokenStore,
) -> None:
    """Révoque toutes les sessions après réutilisation d'un refresh token."""
    try:
        account_id = UUID(subject)
    except ValueError:
        return
    async with database_infrastructure.async_session_factory() as session:
        service = SessionService(SqlAlchemySessionRepository(session))
        refresh_jtis = await service.list_refresh_jtis(account_id)
        await service.revoke_all_sessions(account_id)
        await session.commit()
    for refresh_jti in refresh_jtis:
        await refresh_store.revoke(refresh_jti)


async def _rotate_active_session(
    current_jti: str,
    new_jti: str,
    new_refresh_jti: str,
) -> bool:
    """Met à jour la session DB uniquement pour les refresh tokens canoniques."""
    async with database_infrastructure.async_session_factory() as session:
        service = SessionService(SqlAlchemySessionRepository(session))
        updated = await service.rotate_session(current_jti, new_jti, new_refresh_jti)
        await session.commit()
        return updated


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


SessionVersionValidator = Callable[[UUID, int], Awaitable[bool]]


async def _is_session_version_current(account_id: UUID, session_version: int) -> bool:
    """Ouvre la base uniquement pour les sessions d'identité versionnées."""
    async with database_infrastructure.async_session_factory() as session:
        return await SqlAlchemyIdentityRepository(session).is_session_version_current(
            account_id,
            session_version,
        )


def get_session_version_validator() -> SessionVersionValidator:
    """Dépendance paresseuse, surchargeable sans connexion DB dans les tests."""
    return _is_session_version_current


def _get_dev_user(username: str, password: str) -> DevUser | None:
    """Authentifie un utilisateur de développement via env vars.

    Returns:
        Dict utilisateur si authentifié, None sinon.
    """
    if not _settings.auth_dev_login_enabled:
        return None
    if not _settings.auth_dev_username or not _settings.auth_dev_password:
        return None
    # Comparaison en temps constant (OWASP A02/A07) — évite les attaques
    # par timing même en dev. Les secrets restent en mémoire, jamais loggués.
    if not hmac.compare_digest(
        username.encode("utf-8"),
        _settings.auth_dev_username.encode("utf-8"),
    ):
        return None
    if not hmac.compare_digest(
        password.encode("utf-8"),
        _settings.auth_dev_password.encode("utf-8"),
    ):
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
    client_ip = get_client_address(request)
    user_agent = request.headers.get("User-Agent", "unknown")

    turnstile = TurnstileClient(_settings)
    if not await turnstile.verify(credentials.turnstile_token, client_ip):
        logger.warning(
            "login_turnstile_rejected",
            username=credentials.username,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Turnstile challenge failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
@_limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_request: RefreshRequest,
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
    session_version_validator: Annotated[
        SessionVersionValidator,
        Depends(get_session_version_validator),
    ],
) -> TokenResponse:
    """Échange un refresh token contre un nouveau access token."""
    payload = verify_token(refresh_request.refresh_token, expected_type="refresh")
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
    auth_provider = payload.get("auth_provider")
    if isinstance(auth_provider, str):
        session_claims["auth_provider"] = auth_provider
        session_version = payload.get("session_version")
        try:
            account_id = UUID(subject)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token claims",
            ) from None
        if type(session_version) is not int or not await session_version_validator(
            account_id,
            session_version,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session révoquée",
            )
        session_claims["session_version"] = session_version

    current_session_jti = payload.get("session_jti")
    access_token = create_access_token(subject=subject, claims=session_claims)
    access_payload = verify_token(access_token, expected_type="access")
    refresh_claims = {**session_claims, "session_jti": str(access_payload["jti"])}
    new_refresh_token = create_refresh_token(subject=subject, claims=refresh_claims)
    new_payload = verify_token(new_refresh_token, expected_type="refresh")
    rotated = await refresh_store.rotate(
        jti,
        str(new_payload["jti"]),
        float(new_payload["exp"]),
    )
    if not rotated:
        if _settings.refresh_token_reuse_detection_enabled:
            if isinstance(current_session_jti, str):
                await _revoke_account_sessions(subject, refresh_store)
            logger.warning(
                "refresh_token_reuse_detected",
                jti=jti,
                subject=subject,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or already used",
        )

    if isinstance(current_session_jti, str):
        updated = await _rotate_active_session(
            current_session_jti,
            str(access_payload["jti"]),
            str(new_payload["jti"]),
        )
        if not updated:
            await refresh_store.revoke(str(new_payload["jti"]))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session révoquée",
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
@_limiter.limit("60/minute")
async def verify_access_token(
    request: Request,
    response: Response,
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


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Déconnexion — révocation du refresh token",
    description=(
        "Révoque le refresh token fourni dans le registre. Le access token "
        "actif reste valide jusqu'à son expiration (15 min) — c'est la "
        "limite du JWT sans liste noire centralisée. Le refresh token ne "
        "peut plus être utilisé pour obtenir un nouveau access token."
    ),
)
@_limiter.limit("30/minute")
async def logout(
    request: Request,
    response: Response,
    logout_request: LogoutRequest,
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
) -> LogoutResponse:
    """Révoque un refresh token (consommation atomique dans le registre)."""
    payload = verify_token(logout_request.refresh_token, expected_type="refresh")
    jti = payload.get("jti")
    if not isinstance(jti, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims",
        )
    revoked = await refresh_store.consume(jti)
    logger.info("logout", jti=jti, revoked=revoked)
    return LogoutResponse(revoked=revoked)


class TurnstileVerifyResponse(TypedDict):
    """Résultat d'une vérification Turnstile."""

    valid: bool


@router.post(
    "/turnstile/verify",
    response_model=TurnstileVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Vérifier un token Turnstile",
    description="Vérifie un token Cloudflare Turnstile sans authentification.",
)
@_limiter.limit("20/minute")
async def verify_turnstile_token(
    request: Request,
    response: Response,
    payload: TurnstileVerifyRequest,
) -> TurnstileVerifyResponse:
    """Valide un token Turnstile pour les formulaires front-end."""
    client_ip = get_client_address(request)
    turnstile = TurnstileClient(_settings)
    is_valid = await turnstile.verify(payload.token, client_ip)
    return TurnstileVerifyResponse(valid=is_valid)
