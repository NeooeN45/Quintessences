"""Exceptions du SDK GSIE."""

from __future__ import annotations


class GSIEError(Exception):
    """Erreur de base du SDK GSIE."""


class AuthenticationError(GSIEError):
    """Échec d'authentification (identifiants invalides, token expiré)."""


class TokenRefreshError(GSIEError):
    """Échec du rafraîchissement du token (rotation refusée, jti révoqué)."""


class APIError(GSIEError):
    """Erreur retournée par l'API GSIE (statut HTTP non 2xx)."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"GSIE API {status_code}: {detail}")
