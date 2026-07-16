"""Schémas Pydantic pour l'authentification."""

from pydantic import BaseModel, ConfigDict, Field


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
