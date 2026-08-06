"""Tests unitaires — validation configuration (config.py)."""

import pytest
from pydantic import ValidationError

from gsie_api.core.config import Settings


def should_accept_development_defaults(monkeypatch: pytest.MonkeyPatch):
    """Settings doit accepter les valeurs par défaut en développement.

    Le .env local peut surcharger rate_limit_storage_url (Redis en dev) ;
    on l'isole pour vérifier que la valeur par défaut du code est bien
    "memory://" quand aucune variable d'environnement n'est définie.
    """
    monkeypatch.delenv("GSIE_RATE_LIMIT_STORAGE_URL", raising=False)
    # _env_file=None empêche pydantic-settings de lire le .env local
    settings = Settings(environment="development", debug=False, _env_file=None)
    assert settings.debug is False
    assert settings.rate_limit_storage_url == "memory://"
    assert settings.edge_proxy_mode == "direct"


def should_accept_cloudflare_tunnel_as_edge_proxy_mode() -> None:
    settings = Settings(edge_proxy_mode="cloudflare_tunnel", _env_file=None)

    assert settings.edge_proxy_mode == "cloudflare_tunnel"


def should_reject_an_unknown_edge_proxy_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(edge_proxy_mode="proxy-inconnu", _env_file=None)


def _production_kwargs(**overrides: object) -> dict[str, object]:
    """Retourne les kwargs de base valides pour la production."""
    return {
        "environment": "production",
        "debug": False,
        # Role applicatif dedie : `gsie` est proprietaire de la base, et un
        # proprietaire contourne l'isolement des donnees personnelles
        # (20260728_0012). Une configuration de production valide ne
        # l'emploie pas.
        "database_url": "postgresql+asyncpg://gsie_app:secure@host:5432/gsie",
        "cors_origins": ["https://example.com"],
        "ws_allowed_origins": ["https://hub.example.com"],
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


def should_reject_debug_true_in_production():
    """Settings doit refuser debug=True en production."""
    with pytest.raises(ValidationError, match="debug must be False"):
        Settings(**_production_kwargs(debug=True))


def should_reject_default_db_password_in_production():
    """Settings doit refuser le mot de passe par défaut en production."""
    with pytest.raises(ValidationError, match="Default database password"):
        Settings(
            **_production_kwargs(
                database_url="postgresql+asyncpg://gsie_app:gsie_dev@host:5432/gsie",
            )
        )


def should_reject_wildcard_cors_in_production():
    """Settings doit refuser wildcard CORS en production."""
    with pytest.raises(ValidationError, match="Wildcard CORS"):
        Settings(**_production_kwargs(cors_origins=["*"]))


def should_reject_localhost_cors_in_production():
    """Settings doit refuser localhost CORS en production."""
    with pytest.raises(ValidationError, match="localhost CORS"):
        Settings(**_production_kwargs(cors_origins=["http://localhost:3000"]))


def should_reject_redis_without_password_in_production():
    """Settings doit refuser Redis sans mot de passe en production (OWASP A07)."""
    with pytest.raises(ValidationError, match="Redis without password"):
        Settings(**_production_kwargs(redis_url="redis://localhost:6379/0"))


def should_accept_redis_with_password_in_production():
    """Settings doit accepter Redis avec mot de passe en production."""
    settings = Settings(**_production_kwargs())
    assert "secret" in settings.redis_url


def should_reject_wildcard_ws_origins_in_production():
    """Settings doit refuser les origines WebSocket wildcard en production."""
    with pytest.raises(ValidationError, match="Wildcard WebSocket"):
        Settings(**_production_kwargs(ws_allowed_origins=["*"]))


def should_reject_disabled_tls_in_production():
    """Settings doit refuser db_ssl_mode faible (audit sécurité P0-4)."""
    with pytest.raises(ValidationError, match="TLS PostgreSQL requis"):
        Settings(**_production_kwargs(db_ssl_mode="prefer"))


def should_accept_verify_full_tls_in_production():
    """Settings doit accepter verify-full comme mode TLS strict."""
    settings = Settings(**_production_kwargs(db_ssl_mode="verify-full"))
    assert settings.db_ssl_mode == "verify-full"


def should_reject_local_registration_without_smtp_in_production():
    """Un compte local sans canal de récupération ne doit pas être déployable."""
    with pytest.raises(ValidationError, match="service SMTP"):
        Settings(
            **_production_kwargs(
                transactional_email_mode="disabled",
                smtp_host="",
            )
        )


def should_reject_unencrypted_smtp_in_production():
    """Le transport des codes sensibles doit être chiffré hors développement."""
    with pytest.raises(ValidationError, match="SMTP doit être chiffré"):
        Settings(
            **_production_kwargs(
                smtp_use_tls=False,
                smtp_starttls=False,
            )
        )


def should_reject_direct_tls_and_starttls_together() -> None:
    """Les deux modes de négociation SMTP sont mutuellement exclusifs."""
    with pytest.raises(ValidationError, match="ne peuvent pas être activés ensemble"):
        Settings(
            environment="development",
            smtp_use_tls=True,
            smtp_starttls=True,
            _env_file=None,
        )


def should_reject_smtp_mode_without_relay() -> None:
    """Activer SMTP sans hôte explicite doit échouer dès le démarrage."""
    with pytest.raises(ValidationError, match="GSIE_SMTP_HOST"):
        Settings(
            environment="development",
            transactional_email_mode="smtp",
            smtp_host="",
            _env_file=None,
        )


# ===========================================================================
# Couverture complémentaire — validators production supplémentaires + .env.enc
# ===========================================================================


def should_reject_dev_login_enabled_in_production():
    """Settings doit refuser auth_dev_login_enabled en production."""
    with pytest.raises(ValidationError, match="Development login must be disabled"):
        Settings(
            **_production_kwargs(
                auth_dev_login_enabled=True,
                auth_dev_password="real-password-not-placeholder",
            )
        )


def should_reject_rust_not_required_in_production():
    """Settings doit refuser require_rust_backend=False en production."""
    with pytest.raises(ValidationError, match="Rust Evidence backend must be required"):
        Settings(**_production_kwargs(require_rust_backend=False))


def should_reject_memory_rate_limit_in_production():
    """Settings doit refuser rate_limit_storage_url=memory:// en production."""
    with pytest.raises(ValidationError, match="Distributed rate-limit storage required"):
        Settings(**_production_kwargs(rate_limit_storage_url="memory://"))


def should_reject_memory_refresh_token_in_production():
    """Settings doit refuser refresh_token_storage_url=memory:// en production."""
    with pytest.raises(ValidationError, match="Distributed refresh-token storage required"):
        Settings(**_production_kwargs(refresh_token_storage_url="memory://"))


def should_reject_owner_role_in_production():
    """Settings doit refuser un role propriétaire PostgreSQL en production."""
    with pytest.raises(ValidationError, match="role de connexion"):
        Settings(
            **_production_kwargs(
                database_url="postgresql+asyncpg://gsie:secure@host:5432/gsie",
            )
        )


def should_reject_dev_password_placeholder_when_dev_login_enabled():
    """Settings doit refuser un mot de passe de remplissage quand dev login est activé."""
    with pytest.raises(ValidationError, match="valeur de remplissage"):
        Settings(
            environment="development",
            debug=False,
            auth_dev_login_enabled=True,
            auth_dev_password="changeme",
            _env_file=None,
        )


def should_reject_pool_sizing_incoherent():
    """Settings doit refuser un pool sizing incohérent avec max_connections."""
    with pytest.raises(ValidationError, match="Pool sizing incoherent"):
        Settings(
            environment="development",
            debug=False,
            gunicorn_workers=10,
            db_pool_size=20,
            db_max_overflow=20,
            db_max_connections=5,
            _env_file=None,
        )


def should_return_migration_url_when_set():
    """url_de_migration doit retourner migration_database_url quand défini."""
    settings = Settings(
        environment="development",
        debug=False,
        migration_database_url="postgresql+asyncpg://admin:pass@host:5432/gsie",
        _env_file=None,
    )
    assert settings.url_de_migration == "postgresql+asyncpg://admin:pass@host:5432/gsie"


def should_return_database_url_when_migration_url_not_set():
    """url_de_migration doit retourner database_url quand migration_database_url est None."""
    settings = Settings(
        environment="development",
        debug=False,
        database_url="postgresql+asyncpg://app:pass@host:5432/gsie",
        _env_file=None,
    )
    assert settings.url_de_migration == "postgresql+asyncpg://app:pass@host:5432/gsie"


# --- Tests _parse_env_line ---


def should_parse_env_line_with_double_quotes():
    """_parse_env_line doit retirer les guillemets doubles."""
    from gsie_api.core.config import _parse_env_line

    assert _parse_env_line('KEY="value"') == ("KEY", "value")


def should_parse_env_line_with_single_quotes():
    """_parse_env_line doit retirer les guillemets simples."""
    from gsie_api.core.config import _parse_env_line

    assert _parse_env_line("KEY='value'") == ("KEY", "value")


def should_return_none_for_comment_line():
    """_parse_env_line doit retourner None pour un commentaire."""
    from gsie_api.core.config import _parse_env_line

    assert _parse_env_line("# comment") is None


def should_return_none_for_empty_line():
    """_parse_env_line doit retourner None pour une ligne vide."""
    from gsie_api.core.config import _parse_env_line

    assert _parse_env_line("") is None


def should_return_none_for_line_without_equals():
    """_parse_env_line doit retourner None pour une ligne sans =."""
    from gsie_api.core.config import _parse_env_line

    assert _parse_env_line("no_equals_here") is None


def should_return_none_for_line_with_empty_key():
    """_parse_env_line doit retourner None pour une ligne avec clé vide."""
    from gsie_api.core.config import _parse_env_line

    assert _parse_env_line("=value") is None


# --- Tests _load_encrypted_env ---


def should_load_encrypted_env_when_env_enc_present(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """_load_encrypted_env doit déchiffrer .env.enc quand .env est absent."""
    from cryptography.fernet import Fernet

    import gsie_api.core.config as config_module

    # Génère une clé Fernet
    key = Fernet.generate_key()
    key_file = tmp_path / "secret.key"
    key_file.write_bytes(key)

    # Crée un .env.enc chiffré
    fernet = Fernet(key)
    plaintext = 'DATABASE_URL="postgresql+asyncpg://test:pass@host/db"\nDEBUG=false\n'
    env_enc = tmp_path / ".env.enc"
    env_enc.write_bytes(fernet.encrypt(plaintext.encode()))

    # Mocke les chemins
    monkeypatch.setattr(config_module, "_ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(config_module, "_ENV_ENC_FILE", env_enc)
    monkeypatch.setattr(config_module, "_KEY_FILE", key_file)
    monkeypatch.setattr(config_module, "_decrypted_env_cache", None)

    config_module._load_encrypted_env()

    assert config_module._decrypted_env_cache is not None
    assert "DATABASE_URL" in config_module._decrypted_env_cache
    assert (
        config_module._decrypted_env_cache["DATABASE_URL"]
        == "postgresql+asyncpg://test:pass@host/db"
    )


def should_skip_loading_when_env_file_exists(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """_load_encrypted_env ne doit rien faire si .env existe."""
    import gsie_api.core.config as config_module

    env_file = tmp_path / ".env"
    env_file.write_text("DEBUG=true", encoding="utf-8")

    monkeypatch.setattr(config_module, "_ENV_FILE", env_file)
    monkeypatch.setattr(config_module, "_ENV_ENC_FILE", tmp_path / ".env.enc")
    monkeypatch.setattr(config_module, "_decrypted_env_cache", None)

    config_module._load_encrypted_env()

    assert config_module._decrypted_env_cache is None


def should_skip_loading_when_cache_already_populated(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """_load_encrypted_env doit être idempotent (cache déjà chargé)."""
    import gsie_api.core.config as config_module

    monkeypatch.setattr(config_module, "_decrypted_env_cache", {"KEY": "value"})

    config_module._load_encrypted_env()

    assert config_module._decrypted_env_cache == {"KEY": "value"}


def should_warn_when_key_file_missing(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """_load_encrypted_env doit logger un warning si la clé Fernet est absente."""
    import gsie_api.core.config as config_module

    env_enc = tmp_path / ".env.enc"
    env_enc.write_bytes(b"encrypted data")

    monkeypatch.setattr(config_module, "_ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(config_module, "_ENV_ENC_FILE", env_enc)
    monkeypatch.setattr(config_module, "_KEY_FILE", tmp_path / "nonexistent.key")
    monkeypatch.setattr(config_module, "_decrypted_env_cache", None)

    # Ne doit pas lever — juste logger un warning
    config_module._load_encrypted_env()

    assert config_module._decrypted_env_cache is None


def should_skip_loading_when_env_enc_absent(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """_load_encrypted_env ne doit rien faire si .env.enc est absent."""
    import gsie_api.core.config as config_module

    monkeypatch.setattr(config_module, "_ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(config_module, "_ENV_ENC_FILE", tmp_path / ".env.enc")
    monkeypatch.setattr(config_module, "_decrypted_env_cache", None)

    config_module._load_encrypted_env()

    assert config_module._decrypted_env_cache is None
