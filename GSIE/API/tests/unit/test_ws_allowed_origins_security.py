"""Tests de non-regression -- ws_allowed_origins (validate_production_security).

Contexte (P1-2) : ``ws_allowed_origins`` vaut ``["*"]`` par defaut
(config.py:95) et ``validate_production_security`` (config.py:150-151)
doit lever une erreur si ce wildcard est present en production. Ce
fichier fige ce comportement pour detecter toute regression silencieuse
si le controle venait a etre retire ou affaibli.
"""

import pytest
from pydantic import ValidationError

from gsie_api.core.config import Settings


def _production_kwargs(**overrides: object) -> dict[str, object]:
    """Retourne les kwargs minimaux valides pour instancier Settings en production.

    Toutes les autres contraintes de ``validate_production_security`` sont
    satisfaites afin d'isoler exclusivement le comportement de
    ``ws_allowed_origins``.
    """
    return {
        "environment": "production",
        "debug": False,
        "database_url": "postgresql+asyncpg://gsie_app:secure@host:5432/gsie",
        "cors_origins": ["https://app.gsie.fr"],
        "ws_allowed_origins": ["https://app.gsie.fr"],
        "redis_url": "redis://:secret@redis-host:6379/0",
        "rate_limit_storage_url": "redis://:secret@redis-host:6379/1",
        "refresh_token_storage_url": "redis://:secret@redis-host:6379/2",
        "auth_dev_login_enabled": False,
        "transactional_email_mode": "smtp",
        "smtp_host": "smtp.example.com",
        "require_rust_backend": True,
        "db_ssl_mode": "require",
        "mfa_encryption_key": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
    } | overrides


def should_reject_wildcard_in_production() -> None:
    """validate_production_security rejette ws_allowed_origins=['*'] en prod."""
    # Arrange
    kwargs = _production_kwargs(ws_allowed_origins=["*"])

    # Act & Assert
    with pytest.raises(ValidationError, match="Wildcard WebSocket"):
        Settings(**kwargs)


def should_accept_explicit_origins_in_production() -> None:
    """validate_production_security doit accepter une origine explicite en production."""
    # Arrange
    kwargs = _production_kwargs(ws_allowed_origins=["https://app.gsie.fr"])

    # Act
    settings = Settings(**kwargs)

    # Assert
    assert settings.ws_allowed_origins == ["https://app.gsie.fr"]


def should_accept_wildcard_in_development() -> None:
    """Le wildcard ws_allowed_origins reste autorise en developpement."""
    # Arrange
    kwargs: dict[str, object] = {
        "environment": "development",
        "debug": False,
        "ws_allowed_origins": ["*"],
    }

    # Act
    settings = Settings(**kwargs)

    # Assert
    assert settings.ws_allowed_origins == ["*"]


def should_accept_empty_list() -> None:
    """Une liste vide de ws_allowed_origins doit etre acceptee (aucun wildcard present).

    Ce test documente le comportement actuel du code : une liste vide ne
    contient pas '*', donc ``validate_production_security`` ne leve pas
    d'erreur, meme si fonctionnellement cela desactive tout WebSocket.
    """
    # Arrange
    kwargs = _production_kwargs(ws_allowed_origins=[])

    # Act
    settings = Settings(**kwargs)

    # Assert
    assert settings.ws_allowed_origins == []
