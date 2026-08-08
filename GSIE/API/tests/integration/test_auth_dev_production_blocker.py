"""Tests d'intégration anti-régression — blocage du login dev en production.

Contexte (P1-1) : `auth/router.py::_get_dev_user` compare le mot de passe en
clair, sans `bcrypt.checkpw`. La mitigation actuelle repose entièrement sur
`Settings.validate_production_security` (core/config.py) qui interdit
`auth_dev_login_enabled=True` dès que `environment` vaut "production" ou
"staging". Ce fichier verrouille cette mitigation : si un jour la validation
disparaît ou est affaiblie, ces tests doivent échouer immédiatement.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from gsie_api.app import create_app
from gsie_api.auth import router as auth_router
from gsie_api.core.config import Settings


def _production_kwargs(**overrides: object) -> dict[str, object]:
    """Kwargs de base valides pour une configuration de production.

    Repris de `tests/unit/test_config.py::_production_kwargs` pour ne
    déclencher que la règle testée (isolation des cas).
    """
    return {
        "environment": "production",
        "debug": False,
        # Role applicatif dedie, non proprietaire : `gsie` est le
        # proprietaire, et un proprietaire PostgreSQL contourne l'isolement
        # des donnees personnelles (20260728_0012). Une configuration de
        # production **valide** ne l'emploie donc pas.
        "database_url": "postgresql+asyncpg://gsie_app:secure@host:5432/gsie",
        "cors_origins": ["https://example.com"],
        "ws_allowed_origins": ["https://hub.example.com"],
        "redis_url": "redis://:secret@redis-host:6379/0",
        "rate_limit_storage_url": "redis://:secret@redis-host:6379/1",
        "refresh_token_storage_url": "redis://:secret@redis-host:6379/2",
        "auth_dev_login_enabled": False,
        "auth_dev_password": "mot_de_passe_reel_pour_tests_integration",
        "require_rust_backend": True,
        "db_ssl_mode": "require",
        # MFA est active par défaut (mfa_enabled=True), la production exige
        # une clé de chiffrement pour les secrets TOTP (DEC-000052).
        "mfa_encryption_key": "test-integration-mfa-key-32bytes-min!!",
        # La création de comptes locaux est active par défaut, la production
        # exige un service SMTP configuré avec chiffrement.
        "transactional_email_mode": "smtp",
        "smtp_host": "smtp.example.com",
        "smtp_starttls": True,
    } | overrides


def should_raise_on_startup_when_production_and_dev_auth_enabled() -> None:
    """La configuration doit échouer si le login dev est actif en production."""
    # Arrange
    kwargs = _production_kwargs(auth_dev_login_enabled=True)

    # Act / Assert
    with pytest.raises(ValidationError, match="Development login must be disabled"):
        Settings(**kwargs)


def should_not_raise_when_production_and_dev_auth_disabled() -> None:
    """La configuration doit être acceptée en production quand le login dev est désactivé."""
    # Arrange
    kwargs = _production_kwargs(auth_dev_login_enabled=False)

    # Act
    settings = Settings(**kwargs)

    # Assert
    assert settings.auth_dev_login_enabled is False
    assert settings.environment == "production"


def should_not_raise_when_development_and_dev_auth_enabled() -> None:
    """Le login dev doit rester autorisé en développement (usage normal)."""
    # Arrange / Act
    settings = Settings(
        environment="development",
        debug=False,
        auth_dev_login_enabled=True,
        auth_dev_password="mot_de_passe_reel_pour_tests_integration",
    )

    # Assert
    assert settings.auth_dev_login_enabled is True
    assert settings.environment == "development"


def should_reject_dev_login_when_disabled() -> None:
    """L'endpoint /auth/dev/login doit être fermé quand auth_dev_login_enabled=False.

    Fake in-process : on bascule le singleton de settings utilisé par le
    router (comme `tests/unit/test_auth.py` le fait pour le mot de passe)
    plutôt que de mocker la dépendance — pas de double du comportement réel.
    """
    # Arrange
    original_enabled = auth_router._settings.auth_dev_login_enabled
    original_username = auth_router._settings.auth_dev_username
    original_password = auth_router._settings.auth_dev_password
    auth_router._settings.auth_dev_login_enabled = False
    auth_router._settings.auth_dev_username = "admin"
    auth_router._settings.auth_dev_password = "changeme"
    client = TestClient(create_app())

    try:
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme"},
        )

        # Assert
        assert response.status_code in (403, 404)
    finally:
        auth_router._settings.auth_dev_login_enabled = original_enabled
        auth_router._settings.auth_dev_username = original_username
        auth_router._settings.auth_dev_password = original_password


# --- Le role de connexion ne doit pas etre proprietaire de la base ---


def should_refuse_production_when_connecting_as_database_owner() -> None:
    """Un propriétaire PostgreSQL contourne l'isolement des données personnelles.

    `20260728_0011` place `data_subject` — le mécanisme de réversion du
    pseudonymat — dans un schéma dont les droits sont retirés à `PUBLIC`. Mais
    PostgreSQL accorde au **propriétaire** des droits implicites que `REVOKE`
    n'ôte pas : établi par
    `test_isolement_rgpd.py::test_le_proprietaire_de_la_base_contourne_l_isolement`.

    L'isolement était donc disponible sans être en vigueur, l'application se
    connectant avec `gsie`. Cette garde refuse cette configuration en
    production, comme la garde voisine refuse le mot de passe par défaut.
    """
    with pytest.raises(ValidationError, match="proprietaire de la base"):
        Settings(
            **_production_kwargs(
                database_url="postgresql+asyncpg://gsie:motdepasse_solide@host:5432/gsie"
            )  # type: ignore[arg-type]
        )


def should_accept_production_with_a_non_owner_role() -> None:
    """Un rôle applicatif dédié passe.

    Sans ce contrôle, refuser toute configuration ferait passer le test
    précédent et rendrait la production impossible à démarrer.
    """
    reglages = Settings(
        **_production_kwargs(
            database_url="postgresql+asyncpg://gsie_app:motdepasse_solide@host:5432/gsie"
        )  # type: ignore[arg-type]
    )

    assert "gsie_app" in reglages.database_url
