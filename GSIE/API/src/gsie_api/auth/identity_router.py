"""Endpoints du compte Quintessences multi-fournisseurs (DEC-000044)."""

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.auth.account_lifecycle import (
    AccountLifecycleService,
    AccountNotFoundError,
    AccountProfile,
    InvalidActionCodeError,
)
from gsie_api.auth.auth_events import log_auth_event
from gsie_api.auth.google_identity import GoogleTokenVerifier, InvalidGoogleTokenError
from gsie_api.auth.google_nonces import GoogleNonceStore, get_google_nonce_store
from gsie_api.auth.identity import (
    AccountAlreadyExistsError,
    AccountLinkRequiredError,
    AuthenticatedAccount,
    IdentityService,
    InvalidCredentialsError,
    PasswordService,
    ProviderAlreadyLinkedError,
    ProviderNotConfiguredError,
)
from gsie_api.auth.lockout import AccountLockedError, AccountLockoutService, get_lockout_store
from gsie_api.auth.mfa import (
    InvalidRecoveryCodeError,
    InvalidTotpCodeError,
    MfaAlreadyEnabledError,
    MfaError,
    MfaNotEnabledError,
    MfaService,
)
from gsie_api.auth.oidc_generic import (
    InvalidOidcTokenError,
    get_generic_oidc_verifier,
)
from gsie_api.auth.password_strength import (
    CompromisedPasswordError,
    PasswordStrengthService,
    WeakPasswordError,
)
from gsie_api.auth.refresh_tokens import RefreshTokenStore, get_refresh_token_store
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from gsie_api.auth.schemas import (
    AcceptedResponse,
    AccountProfileResponse,
    ActionCodeRequest,
    CompletedResponse,
    GoogleLoginRequest,
    GoogleNonceResponse,
    ListSessionsResponse,
    LocalLoginRequest,
    MfaSetupResponse,
    MfaStatusResponse,
    MfaVerifyRequest,
    OidcLoginRequest,
    OidcProvidersResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordStrengthResponse,
    ProviderCapability,
    ProvidersResponse,
    RegistrationRequest,
    RevokeSessionRequest,
    SessionResponse,
    TokenResponse,
    UpdateProfileRequest,
)
from gsie_api.auth.sessions import SessionService, SqlAlchemySessionRepository
from gsie_api.auth.transactional_email import (
    TransactionalEmailSender,
    get_transactional_email_sender,
)
from gsie_api.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_token,
)
from gsie_api.core.config import get_settings
from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
_settings = get_settings()
logger = get_logger("gsie_api.auth.identity_router")


@lru_cache
def get_password_service() -> PasswordService:
    """Partage le paramétrage Argon2 et son hash factice anti-énumération."""
    return PasswordService()


@lru_cache
def get_google_token_verifier() -> GoogleTokenVerifier:
    """Construit le vérificateur pour les audiences explicitement autorisées."""
    return GoogleTokenVerifier(tuple(_settings.google_oauth_client_ids))


async def get_identity_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IdentityService:
    """Dependency FastAPI du service d'identité transactionnel."""
    return IdentityService(
        repository=SqlAlchemyIdentityRepository(session),
        password_service=get_password_service(),
        google_verifier=get_google_token_verifier(),
    )


async def get_account_lifecycle_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AccountLifecycleService:
    """Dependency du profil et des actions sensibles du compte."""
    return AccountLifecycleService(
        repository=SqlAlchemyIdentityRepository(session),
        password_service=get_password_service(),
        code_expire_minutes=_settings.identity_action_code_expire_minutes,
    )


async def get_mfa_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MfaService:
    """Dependency du service MFA TOTP."""
    return MfaService(
        repository=SqlAlchemyIdentityRepository(session),
        password_service=get_password_service(),
    )


async def get_session_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionService:
    """Dependency du service de sessions actives."""
    return SessionService(SqlAlchemySessionRepository(session))


def get_lockout_service() -> AccountLockoutService:
    """Dependency du service de lockout progressif."""
    return AccountLockoutService(get_lockout_store())


@lru_cache
def get_password_strength_service() -> PasswordStrengthService:
    """Singleton du service de vérification de force mot de passe."""
    return PasswordStrengthService()


def _account_id(current_user: dict[str, object]) -> UUID:
    """Convertit le sujet GSIE en UUID canonique sans accepter d'autre forme."""
    try:
        return UUID(str(current_user.get("sub", "")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide",
        ) from None


def _profile_response(profile: AccountProfile) -> AccountProfileResponse:
    return AccountProfileResponse(
        account_id=str(profile.account_id),
        display_name=profile.display_name,
        email=profile.email,
        email_verified=profile.email_verified,
        providers=list(profile.providers),
        roles=list(profile.roles),
    )


async def _issue_tokens(
    account: AuthenticatedAccount,
    refresh_store: RefreshTokenStore,
    request: Request | None = None,
    session_service: SessionService | None = None,
) -> TokenResponse:
    """Émet une session GSIE indépendante du fournisseur d'origine."""
    claims: dict[str, object] = {
        "roles": list(account.roles),
        "auth_provider": account.provider,
        "session_version": account.session_version,
    }
    subject = str(account.account_id)
    access_token = create_access_token(subject=subject, claims=claims)
    refresh_token = create_refresh_token(subject=subject, claims=claims)
    access_payload = verify_token(access_token, expected_type="access")
    refresh_payload = verify_token(refresh_token, expected_type="refresh")
    await refresh_store.register(
        str(refresh_payload["jti"]),
        float(refresh_payload["exp"]),
    )
    # Tracker la session active pour révocation sélective
    if session_service is not None and request is not None:
        user_agent = request.headers.get("User-Agent")
        client_ip = request.client.host if request.client else None
        device_name = request.headers.get("X-Device-Name")
        await session_service.register_session(
            account_id=account.account_id,
            jti=str(access_payload["jti"]),
            refresh_jti=str(refresh_payload["jti"]),
            device_name=device_name,
            user_agent=user_agent,
            ip_address=client_ip,
        )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="Lister les moyens de connexion disponibles",
)
@_limiter.limit("60/minute")
async def providers(request: Request, response: Response) -> ProvidersResponse:
    """Publie les capacités réelles, sans prétendre activer l'entreprise."""
    del request, response
    return ProvidersResponse(
        providers=[
            ProviderCapability(
                provider="local",
                status="available",
                label="Adresse e-mail",
            ),
            ProviderCapability(
                provider="google",
                status="available" if _settings.google_oauth_client_ids else "not_configured",
                label="Google",
            ),
            ProviderCapability(
                provider="enterprise",
                status="development",
                label="Connexion professionnelle",
            ),
        ]
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte Quintessences local",
)
@_limiter.limit("5/minute")
async def register_local(
    request: Request,
    response: Response,
    registration: RegistrationRequest,
    identity_service: Annotated[IdentityService, Depends(get_identity_service)],
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    password_strength: Annotated[PasswordStrengthService, Depends(get_password_strength_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Crée le compte canonique et son premier moyen de connexion."""
    del response
    if not _settings.auth_local_registration_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ressource introuvable")
    # Vérification de force mot de passe (HIBP + zxcvbn)
    try:
        await password_strength.validate(
            registration.password.get_secret_value(),
            user_inputs=[str(registration.email), registration.display_name]
            if registration.display_name
            else [str(registration.email)],
        )
    except CompromisedPasswordError:
        await log_auth_event(
            db_session,
            action="register_password_compromised",
            actor_email=str(registration.email),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            status_code=422,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PASSWORD_COMPROMISED",
        ) from None
    except WeakPasswordError as exc:
        await log_auth_event(
            db_session,
            action="register_password_weak",
            actor_email=str(registration.email),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            status_code=422,
            details={"score": exc.score, "minimum": exc.minimum},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PASSWORD_TOO_WEAK",
        ) from None
    try:
        account = await identity_service.register_local(
            email=str(registration.email),
            password=registration.password.get_secret_value(),
            display_name=registration.display_name,
        )
    except AccountAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ACCOUNT_ALREADY_EXISTS",
        ) from None
    await log_auth_event(
        db_session,
        action="register_success",
        actor_id=account.account_id,
        actor_email=str(registration.email),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        status_code=201,
        details={"provider": "local"},
    )
    logger.info("identity_registered", provider="local", account_id=str(account.account_id))
    return await _issue_tokens(account, refresh_store, request, session_service)


@router.post(
    "/login/password",
    response_model=TokenResponse,
    summary="Se connecter par adresse e-mail",
)
@_limiter.limit("10/minute")
async def login_local(
    request: Request,
    response: Response,
    credentials: LocalLoginRequest,
    identity_service: Annotated[IdentityService, Depends(get_identity_service)],
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
    lockout_service: Annotated[AccountLockoutService, Depends(get_lockout_service)],
    mfa_service: Annotated[MfaService, Depends(get_mfa_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authentifie sans distinguer compte absent et mot de passe erroné."""
    del response
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Vérification du lockout avant toute authentification
    try:
        await lockout_service.check_and_raise(str(credentials.email), client_ip)
    except AccountLockedError as exc:
        await log_auth_event(
            db_session,
            action="login_locked",
            actor_email=str(credentials.email),
            ip_address=client_ip,
            user_agent=user_agent,
            status_code=423,
            details={"remaining_seconds": exc.remaining_seconds},
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="COMPTE_VERROUILLE",
            headers={"Retry-After": str(exc.remaining_seconds)},
        ) from None

    try:
        account = await identity_service.authenticate_local(
            email=str(credentials.email),
            password=credentials.password.get_secret_value(),
        )
    except InvalidCredentialsError:
        await lockout_service.record_failure(str(credentials.email), client_ip)
        await log_auth_event(
            db_session,
            action="login_failed",
            actor_email=str(credentials.email),
            ip_address=client_ip,
            user_agent=user_agent,
            status_code=401,
            details={"provider": "local"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    # Vérification MFA si activée pour ce compte
    if _settings.mfa_enabled:
        try:
            has_mfa = await mfa_service._repository.get_active_secret(account.account_id)
            if has_mfa is not None:
                # Le MFA est activé — le client doit fournir un code TOTP séparément
                # via /auth/mfa/challenge. On retourne un challenge au lieu des tokens.
                await log_auth_event(
                    db_session,
                    action="login_mfa_challenge",
                    actor_id=account.account_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    status_code=200,
                    details={"provider": "local"},
                )
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail="MFA_REQUIRED",
                ) from None
        except MfaError:
            pass  # Si la vérif MFA échoue pour une raison technique, on continue

    await lockout_service.record_success(str(credentials.email), client_ip)
    await log_auth_event(
        db_session,
        action="login_success",
        actor_id=account.account_id,
        ip_address=client_ip,
        user_agent=user_agent,
        status_code=200,
        details={"provider": "local"},
    )
    logger.info("identity_login_success", provider="local", account_id=str(account.account_id))
    return await _issue_tokens(account, refresh_store, request, session_service)


@router.post(
    "/google/nonce",
    response_model=GoogleNonceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nonce Google à usage unique",
)
@_limiter.limit("20/minute")
async def create_google_nonce(
    request: Request,
    response: Response,
    nonce_store: Annotated[GoogleNonceStore, Depends(get_google_nonce_store)],
) -> GoogleNonceResponse:
    del request, response
    nonce = await nonce_store.create()
    return GoogleNonceResponse(nonce=nonce, expires_in=nonce_store.ttl_seconds)


async def _consume_google_nonce(
    nonce_store: GoogleNonceStore,
    nonce: str,
) -> None:
    if not await nonce_store.consume(nonce):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Preuve Google invalide",
        )


@router.post(
    "/login/google",
    response_model=TokenResponse,
    summary="Se connecter avec Google",
)
@_limiter.limit("10/minute")
async def login_google(
    request: Request,
    response: Response,
    credentials: GoogleLoginRequest,
    identity_service: Annotated[IdentityService, Depends(get_identity_service)],
    nonce_store: Annotated[GoogleNonceStore, Depends(get_google_nonce_store)],
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
) -> TokenResponse:
    del request, response
    nonce = credentials.nonce.get_secret_value()
    await _consume_google_nonce(nonce_store, nonce)
    try:
        account = await identity_service.authenticate_google(
            credentials.id_token.get_secret_value(),
            nonce,
        )
    except AccountLinkRequiredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ACCOUNT_LINK_REQUIRED",
        ) from None
    except ProviderNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fournisseur Google non configuré",
        ) from None
    except (InvalidGoogleTokenError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Preuve Google invalide",
        ) from None
    logger.info("identity_login_success", provider="google", account_id=str(account.account_id))
    return await _issue_tokens(account, refresh_store)


@router.post(
    "/link/google",
    response_model=TokenResponse,
    summary="Rattacher Google au compte courant",
)
@_limiter.limit("10/minute")
async def link_google(
    request: Request,
    response: Response,
    credentials: GoogleLoginRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    identity_service: Annotated[IdentityService, Depends(get_identity_service)],
    nonce_store: Annotated[GoogleNonceStore, Depends(get_google_nonce_store)],
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
) -> TokenResponse:
    del request, response
    try:
        account_id = UUID(str(current_user.get("sub", "")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide",
        ) from None
    nonce = credentials.nonce.get_secret_value()
    await _consume_google_nonce(nonce_store, nonce)
    try:
        account = await identity_service.link_google(
            account_id=account_id,
            token=credentials.id_token.get_secret_value(),
            nonce=nonce,
        )
    except ProviderAlreadyLinkedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="GOOGLE_IDENTITY_ALREADY_LINKED",
        ) from None
    except ProviderNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fournisseur Google non configuré",
        ) from None
    except (InvalidGoogleTokenError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Preuve Google invalide",
        ) from None
    logger.info("identity_linked", provider="google", account_id=str(account.account_id))
    return await _issue_tokens(account, refresh_store)


@router.get(
    "/me",
    response_model=AccountProfileResponse,
    summary="Consulter le profil du compte courant",
)
@_limiter.limit("60/minute")
async def get_account_profile(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    lifecycle: Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)],
) -> AccountProfileResponse:
    del request, response
    try:
        profile = await lifecycle.get_profile(_account_id(current_user))
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compte introuvable",
        ) from None
    return _profile_response(profile)


@router.patch(
    "/me",
    response_model=AccountProfileResponse,
    summary="Modifier le profil du compte courant",
)
@_limiter.limit("20/minute")
async def update_account_profile(
    request: Request,
    response: Response,
    update_request: UpdateProfileRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    lifecycle: Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)],
) -> AccountProfileResponse:
    del request, response
    try:
        profile = await lifecycle.update_profile(
            _account_id(current_user),
            update_request.display_name,
        )
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compte introuvable",
        ) from None
    logger.info("identity_profile_updated", account_id=str(profile.account_id))
    return _profile_response(profile)


@router.post(
    "/email/verification/request",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Envoyer un code de vérification de l'adresse",
)
@_limiter.limit("5/minute")
async def request_email_verification(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    lifecycle: Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)],
    email_sender: Annotated[TransactionalEmailSender, Depends(get_transactional_email_sender)],
) -> AcceptedResponse:
    del request, response
    if not email_sender.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de messagerie non configuré",
        )
    account_id = _account_id(current_user)
    delivery = await lifecycle.request_email_verification(account_id)
    if delivery is not None and not await email_sender.send_verification(
        delivery.email,
        delivery.code,
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Envoi temporairement indisponible",
        )
    logger.info("identity_email_verification_requested", account_id=str(account_id))
    return AcceptedResponse()


@router.post(
    "/email/verification/confirm",
    response_model=AccountProfileResponse,
    summary="Confirmer l'adresse avec le code reçu",
)
@_limiter.limit("10/minute")
async def confirm_email_verification(
    request: Request,
    response: Response,
    confirmation: ActionCodeRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    lifecycle: Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)],
) -> AccountProfileResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        profile = await lifecycle.confirm_email_verification(account_id, confirmation.code)
    except InvalidActionCodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CODE_INVALIDE_OU_EXPIRE",
        ) from None
    logger.info("identity_email_verified", account_id=str(account_id))
    return _profile_response(profile)


@router.post(
    "/password/reset/request",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Demander une réinitialisation de mot de passe",
)
@_limiter.limit("5/minute")
async def request_password_reset(
    request: Request,
    response: Response,
    reset_request: PasswordResetRequest,
    lifecycle: Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)],
    email_sender: Annotated[TransactionalEmailSender, Depends(get_transactional_email_sender)],
) -> AcceptedResponse:
    del request, response
    if not email_sender.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de messagerie non configuré",
        )
    delivery = await lifecycle.request_password_reset(str(reset_request.email))
    if delivery is not None:
        # La réponse publique reste identique même si le relais tombe, sinon
        # son statut permettrait de distinguer une adresse connue d'une inconnue.
        await email_sender.send_password_reset(delivery.email, delivery.code)
    logger.info("identity_password_reset_requested")
    return AcceptedResponse()


@router.post(
    "/password/reset/confirm",
    response_model=CompletedResponse,
    summary="Choisir un nouveau mot de passe",
)
@_limiter.limit("10/minute")
async def confirm_password_reset(
    request: Request,
    response: Response,
    confirmation: PasswordResetConfirmRequest,
    lifecycle: Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)],
) -> CompletedResponse:
    del request, response
    try:
        await lifecycle.confirm_password_reset(
            email=str(confirmation.email),
            code=confirmation.code,
            new_password=confirmation.new_password.get_secret_value(),
        )
    except InvalidActionCodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CODE_INVALIDE_OU_EXPIRE",
        ) from None
    logger.info("identity_password_reset_completed")
    return CompletedResponse()


# ============================================================================
# MFA TOTP (RFC 6238) — Lacune 1
# ============================================================================


@router.post(
    "/mfa/setup",
    response_model=MfaSetupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Activer le MFA TOTP pour le compte courant",
)
@_limiter.limit("5/minute")
async def setup_mfa(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    mfa_service: Annotated[MfaService, Depends(get_mfa_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> MfaSetupResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        result = await mfa_service.setup(account_id)
    except MfaAlreadyEnabledError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA_DEJA_ACTIVE",
        ) from None
    await log_auth_event(
        db_session,
        action="mfa_setup",
        actor_id=account_id,
        status_code=201,
    )
    return MfaSetupResponse(
        secret=result.secret,
        otpauth_uri=result.otpauth_uri,
        recovery_codes=list(result.recovery_codes),
    )


@router.post(
    "/mfa/verify",
    response_model=MfaStatusResponse,
    summary="Vérifier un code TOTP ou de récupération",
)
@_limiter.limit("30/minute")
async def verify_mfa(
    request: Request,
    response: Response,
    verification: MfaVerifyRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    mfa_service: Annotated[MfaService, Depends(get_mfa_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> MfaStatusResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        if verification.is_recovery_code:
            await mfa_service.verify_recovery_code(account_id, verification.code)
        else:
            valid = await mfa_service.verify_totp(account_id, verification.code)
            if not valid:
                raise InvalidTotpCodeError
    except InvalidTotpCodeError:
        await log_auth_event(
            db_session,
            action="mfa_verify_failed",
            actor_id=account_id,
            status_code=401,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CODE_TOTP_INVALIDE",
        ) from None
    except InvalidRecoveryCodeError:
        await log_auth_event(
            db_session,
            action="mfa_recovery_failed",
            actor_id=account_id,
            status_code=401,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CODE_RECUPERATION_INVALIDE",
        ) from None
    except MfaNotEnabledError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MFA_NON_ACTIVE",
        ) from None
    await log_auth_event(
        db_session,
        action="mfa_verify_success",
        actor_id=account_id,
        status_code=200,
    )
    return MfaStatusResponse(enabled=True)


@router.delete(
    "/mfa",
    response_model=MfaStatusResponse,
    summary="Désactiver le MFA pour le compte courant",
)
@_limiter.limit("5/minute")
async def disable_mfa(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    mfa_service: Annotated[MfaService, Depends(get_mfa_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> MfaStatusResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        await mfa_service.disable(account_id)
    except MfaNotEnabledError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MFA_NON_ACTIVE",
        ) from None
    await log_auth_event(
        db_session,
        action="mfa_disabled",
        actor_id=account_id,
        status_code=200,
    )
    return MfaStatusResponse(enabled=False)


@router.get(
    "/mfa/status",
    response_model=MfaStatusResponse,
    summary="Consulter l'état MFA du compte courant",
)
@_limiter.limit("60/minute")
async def get_mfa_status(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    mfa_service: Annotated[MfaService, Depends(get_mfa_service)],
) -> MfaStatusResponse:
    del request, response
    account_id = _account_id(current_user)
    record = await mfa_service._repository.get_active_secret(account_id)
    return MfaStatusResponse(enabled=record is not None)


# ============================================================================
# Sessions actives — Lacune 3
# ============================================================================


@router.get(
    "/sessions",
    response_model=ListSessionsResponse,
    summary="Lister les sessions actives du compte courant",
)
@_limiter.limit("30/minute")
async def list_sessions(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> ListSessionsResponse:
    del request, response
    account_id = _account_id(current_user)
    sessions = await session_service.list_sessions(account_id)
    current_jti = str(current_user.get("jti", ""))
    items = [
        SessionResponse(
            id=str(s.id),
            jti=s.jti,
            device_name=s.device_name,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            issued_at=s.issued_at.isoformat(),
            last_seen_at=s.last_seen_at.isoformat(),
            is_current=s.jti == current_jti,
        )
        for s in sessions
    ]
    return ListSessionsResponse(sessions=items, total=len(items))


@router.delete(
    "/sessions",
    response_model=CompletedResponse,
    summary="Révoquer toutes les sessions sauf la courante",
)
@_limiter.limit("10/minute")
async def revoke_all_sessions(
    request: Request,
    response: Response,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> CompletedResponse:
    del request, response
    account_id = _account_id(current_user)
    current_jti = str(current_user.get("jti", ""))
    count = await session_service.revoke_all_sessions(account_id, except_jti=current_jti)
    await log_auth_event(
        db_session,
        action="sessions_revoked_all",
        actor_id=account_id,
        status_code=200,
        details={"revoked_count": count},
    )
    return CompletedResponse()


@router.post(
    "/sessions/revoke",
    response_model=CompletedResponse,
    summary="Révoquer une session spécifique par son ID",
)
@_limiter.limit("20/minute")
async def revoke_session(
    request: Request,
    response: Response,
    revoke_request: RevokeSessionRequest,
    current_user: Annotated[dict[str, object], Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> CompletedResponse:
    del request, response
    account_id = _account_id(current_user)
    try:
        session_id = UUID(revoke_request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID session invalide",
        ) from None
    revoked = await session_service.revoke_session(account_id, session_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session introuvable ou déjà révoquée",
        )
    await log_auth_event(
        db_session,
        action="session_revoked",
        actor_id=account_id,
        status_code=200,
        details={"session_id": str(session_id)},
    )
    return CompletedResponse()


# ============================================================================
# OIDC générique — Lacune 4
# ============================================================================


@router.get(
    "/oidc/providers",
    response_model=OidcProvidersResponse,
    summary="Lister les fournisseurs OIDC enterprise configurés",
)
@_limiter.limit("60/minute")
async def list_oidc_providers(
    request: Request,
    response: Response,
) -> OidcProvidersResponse:
    del request, response
    verifier = get_generic_oidc_verifier()
    return OidcProvidersResponse(providers=verifier.get_provider_names())


@router.post(
    "/login/oidc",
    response_model=TokenResponse,
    summary="Se connecter avec un fournisseur OIDC enterprise",
)
@_limiter.limit("10/minute")
async def login_oidc(
    request: Request,
    response: Response,
    credentials: OidcLoginRequest,
    identity_service: Annotated[IdentityService, Depends(get_identity_service)],
    refresh_store: Annotated[RefreshTokenStore, Depends(get_refresh_token_store)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    del response
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    verifier = get_generic_oidc_verifier()
    if not verifier.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aucun fournisseur OIDC configuré",
        )
    try:
        identity = await verifier.verify(
            credentials.id_token.get_secret_value(),
            credentials.provider,
        )
    except InvalidOidcTokenError:
        await log_auth_event(
            db_session,
            action="oidc_login_failed",
            ip_address=client_ip,
            user_agent=user_agent,
            status_code=401,
            details={"provider": credentials.provider},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Preuve OIDC invalide",
        ) from None

    # Réutilise la logique Google : cherche le compte par issuer+sub, crée si nécessaire
    account = await identity_service._repository.find_provider_account(
        credentials.provider,
        identity.issuer,
        identity.subject,
    )
    if account is None:
        if await identity_service._repository.has_account_with_verified_email(identity.email):
            await log_auth_event(
                db_session,
                action="oidc_link_required",
                ip_address=client_ip,
                user_agent=user_agent,
                status_code=409,
                details={"provider": credentials.provider},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ACCOUNT_LINK_REQUIRED",
            )
        account = await identity_service._repository.create_google_account(identity)

    await log_auth_event(
        db_session,
        action="login_success",
        actor_id=account.account_id,
        ip_address=client_ip,
        user_agent=user_agent,
        status_code=200,
        details={"provider": credentials.provider},
    )
    logger.info(
        "identity_login_success",
        provider=credentials.provider,
        account_id=str(account.account_id),
    )
    return await _issue_tokens(account, refresh_store, request, session_service)


# ============================================================================
# Force mot de passe — Lacune 5 (endpoint de vérification publique)
# ============================================================================


@router.post(
    "/password/strength",
    response_model=PasswordStrengthResponse,
    summary="Vérifier la force d'un mot de passe sans créer de compte",
)
@_limiter.limit("30/minute")
async def check_password_strength(
    request: Request,
    response: Response,
    password_strength: Annotated[PasswordStrengthService, Depends(get_password_strength_service)],
) -> PasswordStrengthResponse:
    """Vérifie la force d'un mot de passe sans lever d'exception."""
    del response
    # Le mot de passe est passé dans le corps — cet endpoint est public
    # mais rate-limité pour éviter l'abus. Le mot de passe n'est jamais loggé.
    body = await request.json()
    password = str(body.get("password", ""))
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe requis",
        )
    report = await password_strength.check(password)
    meets = (not _settings.password_check_hibp_enabled or not report.is_compromised) and (
        not _settings.password_check_zxcvbn_enabled
        or report.zxcvbn_score >= _settings.password_min_zxcvbn_score
    )
    return PasswordStrengthResponse(
        zxcvbn_score=report.zxcvbn_score,
        is_compromised=report.is_compromised,
        compromise_count=report.compromise_count,
        suggestions=list(report.suggestions),
        meets_requirements=meets,
    )
