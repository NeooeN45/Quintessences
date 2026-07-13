"""Tests unitaires — validation configuration (config.py)."""

import pytest
from pydantic import ValidationError

from gsie_api.core.config import Settings


def should_accept_development_defaults():
    """Settings doit accepter les valeurs par défaut en développement."""
    settings = Settings(environment="development", debug=False)
    assert settings.debug is False
    assert settings.rate_limit_storage_url == "memory://"


def should_reject_debug_true_in_production():
    """Settings doit refuser debug=True en production."""
    with pytest.raises(ValidationError, match="debug must be False"):
        Settings(environment="production", debug=True)


def should_reject_default_db_password_in_production():
    """Settings doit refuser le mot de passe par défaut en production."""
    with pytest.raises(ValidationError, match="Default database password"):
        Settings(
            environment="production",
            debug=False,
            database_url="postgresql+asyncpg://gsie:gsie_dev@host:5432/gsie",
        )


def should_reject_wildcard_cors_in_production():
    """Settings doit refuser wildcard CORS en production."""
    with pytest.raises(ValidationError, match="Wildcard CORS"):
        Settings(
            environment="production",
            debug=False,
            database_url="postgresql+asyncpg://gsie:secure@host:5432/gsie",
            cors_origins=["*"],
        )


def should_reject_localhost_cors_in_production():
    """Settings doit refuser localhost CORS en production."""
    with pytest.raises(ValidationError, match="localhost CORS"):
        Settings(
            environment="production",
            debug=False,
            database_url="postgresql+asyncpg://gsie:secure@host:5432/gsie",
            cors_origins=["http://localhost:3000"],
        )


def should_reject_redis_without_password_in_production():
    """Settings doit refuser Redis sans mot de passe en production (OWASP A07)."""
    with pytest.raises(ValidationError, match="Redis without password"):
        Settings(
            environment="production",
            debug=False,
            database_url="postgresql+asyncpg://gsie:secure@host:5432/gsie",
            cors_origins=["https://example.com"],
            redis_url="redis://localhost:6379/0",
        )


def should_accept_redis_with_password_in_production():
    """Settings doit accepter Redis avec mot de passe en production."""
    settings = Settings(
        environment="production",
        debug=False,
        database_url="postgresql+asyncpg://gsie:secure@host:5432/gsie",
        cors_origins=["https://example.com"],
        redis_url="redis://:secret@redis-host:6379/0",
    )
    assert "secret" in settings.redis_url
