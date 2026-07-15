"""Authentification JWT RS256 (DEC-000019).

Responsabilités :
- Création de tokens access (15 min) et refresh (7 jours)
- Vérification des tokens (signature RS256 + expiration)
- Dependency FastAPI get_current_user pour protéger les endpoints

Sécurité :
- RS256 (asymétrique) — clé privée pour signer, clé publique pour vérifier
- Tokens courts (15 min access) pour limiter l'impact d'un vol
- Refresh token rotatif (7 jours) pour éviter les sessions infinies
- Aucun secret en dur — clés chargées depuis fichiers (config.py)

Note : le modèle utilisateur (DB) sera implémenté en Phase 4 semaine 3.
En attendant, un stub utilisateur est utilisé pour les tests.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger

_settings = get_settings()
logger = get_logger("gsie_api.auth")

# Schéma Bearer pour extraction du token depuis le header Authorization
_security_scheme = HTTPBearer(auto_error=False)


def _load_private_key() -> str:
    """Charge la clé privée RSA depuis le fichier configuré.

    En développement, si le fichier n'existe pas, génère une clé de dev.
    """
    key_path = Path(_settings.jwt_private_key_path)
    if key_path.exists():
        return key_path.read_text(encoding="utf-8")
    if _settings.environment == "production":
        raise RuntimeError(f"JWT private key not found: {key_path}")

    logger.warning("jwt_private_key_not_found_using_dev_key", path=str(key_path))
    return _generate_dev_private_key()


def _load_public_key() -> str:
    """Charge la clé publique RSA depuis le fichier configuré."""
    key_path = Path(_settings.jwt_public_key_path)
    if key_path.exists():
        return key_path.read_text(encoding="utf-8")
    if _settings.environment == "production":
        raise RuntimeError(f"JWT public key not found: {key_path}")

    logger.warning("jwt_public_key_not_found_using_dev_key", path=str(key_path))
    return _generate_dev_public_key()


_dev_private_key: str | None = None
_dev_public_key: str | None = None


def _generate_dev_private_key() -> str:
    """Génère une clé privée RSA de développement (2048 bits)."""
    global _dev_private_key
    if _dev_private_key is None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        _dev_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
    return _dev_private_key


def _generate_dev_public_key() -> str:
    """Génère la clé publique correspondant à la clé privée de dev."""
    global _dev_public_key
    if _dev_public_key is None:
        from cryptography.hazmat.primitives import serialization

        private_key_pem = _generate_dev_private_key().encode("utf-8")
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        private_key = load_pem_private_key(private_key_pem, password=None)
        _dev_public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
    return _dev_public_key


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    """Crée un token d'accès JWT (15 min par défaut).

    Args:
        subject: Identifiant de l'utilisateur (sub claim).
        claims: Claims additionnels (rôles, permissions, etc.).

    Returns:
        Token JWT encodé (RS256).
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iss": _settings.jwt_issuer,
        "aud": _settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=_settings.jwt_access_token_expire_minutes),
        "jti": str(uuid4()),
        "type": "access",
    }
    if claims:
        reserved_claims = payload.keys() & claims.keys()
        if reserved_claims:
            names = ", ".join(sorted(reserved_claims))
            raise ValueError(f"Reserved JWT claims cannot be overridden: {names}")
        payload.update(claims)

    return jwt.encode(payload, _load_private_key(), algorithm=_settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """Crée un refresh token JWT (7 jours par défaut).

    Args:
        subject: Identifiant de l'utilisateur (sub claim).

    Returns:
        Token JWT encodé (RS256).
    """
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iss": _settings.jwt_issuer,
        "aud": _settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(days=_settings.jwt_refresh_token_expire_days),
        "jti": str(uuid4()),
        "type": "refresh",
    }

    return jwt.encode(payload, _load_private_key(), algorithm=_settings.jwt_algorithm)


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Vérifie un token JWT (signature + expiration + type).

    Args:
        token: Token JWT à vérifier.
        expected_type: Type attendu ("access" ou "refresh").

    Returns:
        Payload décodé si le token est valide.

    Raises:
        HTTPException 401 si le token est invalide, expiré ou mauvais type.
    """
    try:
        payload = cast(
            "dict[str, Any]",
            jwt.decode(
                token,
                _load_public_key(),
                algorithms=[_settings.jwt_algorithm],
                audience=_settings.jwt_audience,
                issuer=_settings.jwt_issuer,
                options={"require": ["sub", "iss", "aud", "iat", "exp", "jti", "type"]},
            ),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected {expected_type} token, got {payload.get('type')}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_security_scheme)],
) -> dict[str, Any]:
    """Dependency FastAPI — extrait et vérifie l'utilisateur depuis le token.

    Usage :
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            return {"user": user["sub"]}

    Returns:
        Payload du token (sub, iat, exp, type, claims additionnels).

    Raises:
        HTTPException 401 si pas de token ou token invalide.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_token(credentials.credentials, expected_type="access")
