"""Schémas Pydantic pour l'authentification."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class LoginRequest(BaseModel):
    """Requête de login — username + password."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=255, description="Nom d'utilisateur")
    password: str = Field(min_length=1, max_length=500, description="Mot de passe")


class TokenResponse(BaseModel):
    """Réponse token — access + refresh."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="Durée de vie du access token en secondes")


class RefreshRequest(BaseModel):
    """Requête de refresh — refresh token."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1, description="Refresh token JWT")


class VerifyResponse(BaseModel):
    """Réponse de vérification — statut du token."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    subject: str | None = None
    token_type: str | None = None
    expires_at: str | None = None


class LogoutRequest(BaseModel):
    """Requête de logout — refresh token à révoquer."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1, description="Refresh token JWT à révoquer")


class LogoutResponse(BaseModel):
    """Réponse de logout — confirmation de révocation."""

    model_config = ConfigDict(extra="forbid")

    revoked: bool


class RegistrationRequest(BaseModel):
    """Création d'un compte Quintessences local."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_input_email(cls, value: object) -> object:
        """Retire les espaces avant la validation stricte de l'adresse."""
        return value.strip().casefold() if isinstance(value, str) else value


class LocalLoginRequest(BaseModel):
    """Connexion par adresse e-mail et mot de passe."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_input_email(cls, value: object) -> object:
        return value.strip().casefold() if isinstance(value, str) else value


class GoogleLoginRequest(BaseModel):
    """Preuve Google OIDC liée à un nonce serveur à usage unique."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id_token: SecretStr = Field(min_length=1, max_length=16_384)
    nonce: SecretStr = Field(min_length=32, max_length=256)


class GoogleNonceResponse(BaseModel):
    """Nonce public court, à présenter à Google puis au serveur."""

    model_config = ConfigDict(extra="forbid")

    nonce: str
    expires_in: int = Field(gt=0)


class ProviderCapability(BaseModel):
    """État d'un moyen de connexion publié aux clients."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["local", "google", "enterprise"]
    status: Literal["available", "not_configured", "development"]
    label: str


class ProvidersResponse(BaseModel):
    """Capacités d'authentification réellement disponibles."""

    model_config = ConfigDict(extra="forbid")

    providers: list[ProviderCapability]


class AccountProfileResponse(BaseModel):
    """Profil du compte courant, sans jeton ni secret."""

    model_config = ConfigDict(extra="forbid")

    account_id: str
    display_name: str | None
    email: EmailStr | None
    email_verified: bool
    providers: list[str]
    roles: list[str]


class UpdateProfileRequest(BaseModel):
    """Champs personnels modifiables dans la première tranche."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    display_name: str | None = Field(default=None, max_length=200)


class ActionCodeRequest(BaseModel):
    """Code court reçu exclusivement par e-mail."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str = Field(min_length=8, max_length=9, pattern=r"^[A-Za-z0-9]{4}-?[A-Za-z0-9]{4}$")


class PasswordResetRequest(BaseModel):
    """Demande publique qui répond toujours de façon générique."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_input_email(cls, value: object) -> object:
        return value.strip().casefold() if isinstance(value, str) else value


class PasswordResetConfirmRequest(PasswordResetRequest, ActionCodeRequest):
    """Preuve reçue par e-mail et nouveau mot de passe."""

    new_password: SecretStr = Field(min_length=12, max_length=128)


class AcceptedResponse(BaseModel):
    """Accusé générique, volontairement identique pour tous les comptes."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool = True


class CompletedResponse(BaseModel):
    """Confirmation d'une action de compte terminée."""

    model_config = ConfigDict(extra="forbid")

    completed: bool = True


# --- MFA TOTP (RFC 6238) ---


class MfaSetupResponse(BaseModel):
    """Résultat de l'initialisation MFA — secret + URI + codes de récupération."""

    model_config = ConfigDict(extra="forbid")

    secret: str
    otpauth_uri: str
    recovery_codes: list[str]


class MfaVerifyRequest(BaseModel):
    """Vérification d'un code TOTP ou de récupération."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str = Field(min_length=6, max_length=20)
    is_recovery_code: bool = False


class MfaChallengeRequest(BaseModel):
    """Code TOTP requis pour finaliser une action sensible."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    totp_code: str = Field(min_length=6, max_length=8)


class MfaStatusResponse(BaseModel):
    """État MFA du compte courant."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool


# --- Sessions actives ---


class SessionResponse(BaseModel):
    """Vue d'une session active."""

    model_config = ConfigDict(extra="forbid")

    id: str
    jti: str
    device_name: str | None
    user_agent: str | None
    ip_address: str | None
    issued_at: str
    last_seen_at: str
    is_current: bool = False


class ListSessionsResponse(BaseModel):
    """Liste des sessions actives du compte courant."""

    model_config = ConfigDict(extra="forbid")

    sessions: list[SessionResponse]
    total: int


class RevokeSessionRequest(BaseModel):
    """Révocation d'une session par son ID."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=64)


# --- OIDC générique ---


class OidcLoginRequest(BaseModel):
    """Connexion via un fournisseur OIDC enterprise."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    provider: str = Field(min_length=1, max_length=64)
    id_token: SecretStr = Field(min_length=1, max_length=16_384)


class OidcProvidersResponse(BaseModel):
    """Liste des fournisseurs OIDC enterprise configurés."""

    model_config = ConfigDict(extra="forbid")

    providers: list[str]


# --- Force mot de passe ---


class PasswordStrengthResponse(BaseModel):
    """Rapport de force d'un mot de passe (sans lever d'exception)."""

    model_config = ConfigDict(extra="forbid")

    zxcvbn_score: int = Field(ge=0, le=4)
    is_compromised: bool
    compromise_count: int
    suggestions: list[str]
    meets_requirements: bool
