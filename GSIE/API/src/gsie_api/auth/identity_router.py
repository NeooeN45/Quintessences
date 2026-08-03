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
from gsie_api.auth.refresh_tokens import RefreshTokenStore, get_refresh_token_store
from gsie_api.auth.repository import SqlAlchemyIdentityRepository
from gsie_api.auth.schemas import (
    AcceptedResponse,
    AccountProfileResponse,
    ActionCodeRequest,
    CompletedResponse,
    GoogleLoginRequest,
    GoogleNonceResponse,
    LocalLoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    ProviderCapability,
    ProvidersResponse,
    RegistrationRequest,
    TokenResponse,
    UpdateProfileRequest,
)
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
    refresh_payload = verify_token(refresh_token, expected_type="refresh")
    await refresh_store.register(
        str(refresh_payload["jti"]),
        float(refresh_payload["exp"]),
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
) -> TokenResponse:
    """Crée le compte canonique et son premier moyen de connexion."""
    del request, response
    if not _settings.auth_local_registration_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ressource introuvable")
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
    logger.info("identity_registered", provider="local", account_id=str(account.account_id))
    return await _issue_tokens(account, refresh_store)


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
) -> TokenResponse:
    """Authentifie sans distinguer compte absent et mot de passe erroné."""
    del request, response
    try:
        account = await identity_service.authenticate_local(
            email=str(credentials.email),
            password=credentials.password.get_secret_value(),
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    logger.info("identity_login_success", provider="local", account_id=str(account.account_id))
    return await _issue_tokens(account, refresh_store)


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
