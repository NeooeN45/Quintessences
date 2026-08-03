# GSIE API — Configuration
# Les valeurs sont lues depuis les variables d'environnement (.env chiffré
# ou .env en clair pour backward-compat). Aucun secret n'est commité
# (CON-008 souveraineté, global_rules security).

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# Roles proprietaires de la base : PostgreSQL leur accorde des droits
# implicites que `REVOKE` n'ote pas. Une application connectee sous l'un
# d'eux contourne l'isolement des donnees personnelles sans qu'aucune erreur
# ne le signale — verifie par
# `tests/integration/test_isolement_rgpd.py::test_le_proprietaire_de_la_base_contourne_l_isolement`.
#
# Le controle porte sur le nom parce que la configuration est validee avant
# toute connexion : demander a la base « suis-je proprietaire ? » supposerait
# de s'y connecter d'abord. C'est une convention, assumee comme telle, et du
# meme ordre que le refus du mot de passe par defaut juste au-dessus.
_ROLES_PROPRIETAIRES = frozenset({"gsie", "postgres"})

# Valeurs de remplissage livrées par `.env.example` ou choisies par réflexe.
# Le dev login accorde `roles=["admin"]` : laisser passer l'une d'elles revient
# à publier un compte administrateur. Le contrôle vaut dans tous les
# environnements — c'est justement en développement que le mot de passe reste
# celui de l'exemple, et un poste de développement est joignable.
_MOTS_DE_PASSE_DE_REMPLISSAGE = frozenset(
    {
        "",
        "change-me-in-.env",
        "change-me",
        "changeme",
        "admin",
        "password",
        "motdepasse",
        "secret",
    }
)


class _DecryptedEnvSource(PydanticBaseSettingsSource):
    """Source de settings lisant le cache .env.enc déchiffré en mémoire.

    Cette source évite d'injecter les secrets dans ``os.environ`` (qui les
    exposerait aux sous-processus via /proc/self/environ sur Linux). Elle lit
    directement ``_decrypted_env_cache`` rempli par ``_load_encrypted_env()``.
    """

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls)

    def get_field_value(self, field: object, field_name: str) -> tuple[Any, str, bool]:
        """Retourne (valeur, clé d'origine, complex_val) pour un champ."""
        cache = _decrypted_env_cache or {}
        # pydantic-settings préfixe les clés env avec env_prefix.
        prefix = self.config.get("env_prefix", "")
        env_key = f"{prefix}{field_name}"
        if env_key in cache:
            return cache[env_key], env_key, False
        # Cas insensitive (pydantic-settings lit env en case-insensitive).
        env_key_lower = env_key.lower()
        for k, v in cache.items():
            if k.lower() == env_key_lower:
                return v, k, False
        return None, env_key, False

    def prepare_field_value(
        self, field_name: str, field: object, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        cache = _decrypted_env_cache or {}
        prefix = self.config.get("env_prefix", "")
        result: dict[str, Any] = {}
        for key, val in cache.items():
            if key.startswith(prefix):
                field_name = key[len(prefix) :]
                result[field_name] = val
        return result


class Settings(BaseSettings):
    """Configuration globale de l'API GSIE.

    Toutes les valeurs sont surchargeables via variables d'environnement
    ou fichier .env (non commité).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GSIE_",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Ajoute la source .env.enc déchiffrée en mémoire (priorité entre env et dotenv).

        Ordre de priorité (du plus fort au plus faible) :
        1. init_settings (kwargs explicites du constructeur)
        2. env_settings (variables d'environnement réelles — os.environ)
        3. _DecryptedEnvSource (.env.enc déchiffré en mémoire, jamais os.environ)
        4. dotenv_settings (.env en clair, backward-compat)
        5. file_secret_settings (secrets files pydantic, non utilisé ici)
        """
        return (
            init_settings,
            env_settings,
            _DecryptedEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    # Application
    app_name: str = "GSIE API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:4000",
            "http://localhost:8080",
            "http://127.0.0.1:4000",
        ]
    )
    # Limite taille corps de requête (bytes) — défaut 1 MiB (OWASP A04)
    max_request_body_size: int = 1_048_576

    # Rate limiting (OWASP A07 — slowapi)
    rate_limit_enabled: bool = True
    # Format slowapi : "count/period" — défaut 60 req/min par IP
    rate_limit_default: str = "60/minute"
    # Endpoints health/ready plus permissifs (monitoring)
    rate_limit_health: str = "300/minute"
    # Endpoints POST plus stricts (protection flood)
    rate_limit_evaluate: str = "30/minute"
    # Ingestion en lot — 600 req/min (vs 30 pour le unitaire).
    # Conçu pour l'ingestion de datasets externes (Treekipedia, BD Forêt IGN).
    # 600 req/min × 1000 items/lot = 600 000 items/min — suffisant pour
    # 67 928 espèces Treekipedia en ~7 minutes (vs ~200 jours en unitaire).
    rate_limit_bulk: str = "600/minute"

    # PostgreSQL + PostGIS
    # Format : postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "postgresql+asyncpg://gsie:gsie_dev@localhost:5432/gsie"
    # URL de migration — distincte parce que le compte d'exécution ne doit
    # plus pouvoir faire de DDL. `gsie_application` n'a ni CREATE ni ALTER :
    # Alembic doit se connecter sous le compte d'administration. Vide, on
    # retombe sur `database_url` (poste de développement, tests).
    migration_database_url: str = ""
    # Pool sizing par worker Gunicorn :
    # workers × (pool_size + max_overflow) = connexions max applicatives.
    # Doit rester <= db_max_connections - 6 (reserve outbox-worker + admin).
    db_pool_size: int = 4
    db_max_overflow: int = 10
    db_echo: bool = False
    db_pool_timeout: int = 30  # secondes
    # Nombre de workers Gunicorn (doit correspondre à gunicorn.conf.py)
    gunicorn_workers: int = 5
    # max_connections configuré côté PostgreSQL (postgresql.conf / docker-compose)
    db_max_connections: int = 100

    # PgBouncer — statement_cache_size=0 requis (DEC-000019 ajustement P0)
    db_pgbouncer_mode: bool = False
    # TLS PostgreSQL (audit sécurité 2026-07-27 P0-4). Valeurs asyncpg :
    # "disable" | "allow" | "prefer" | "require" | "verify-ca" | "verify-full".
    # "prefer" par défaut en développement ; require+ obligatoire en staging/prod.
    db_ssl_mode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = (
        "prefer"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20
    # Timeouts Redis (secondes) — évite les requêtes bloquantes (résilience P0)
    redis_socket_timeout: float = 5.0
    redis_connect_timeout: float = 5.0
    # Cache TTL pour /ready (secondes) — évite de pinger DB+Redis à chaque requête
    health_cache_ttl: int = 5
    # Rate limit stocké dans Redis (DB 1) pour distribution entre workers
    # En développement/test, "memory://" est utilisé (pas de Redis requis)
    rate_limit_storage_url: str = "memory://"
    # Registre de rotation des refresh tokens. Redis est obligatoire en
    # staging/production pour garantir l'usage unique entre workers.
    refresh_token_storage_url: str = "memory://"

    # Livraison transactionnelle des événements (ADR-005).
    outbox_batch_size: int = Field(default=100, ge=1, le=1000)
    outbox_poll_interval_seconds: float = Field(default=1.0, ge=0.1, le=60.0)
    # Reprise sur échec — backoff exponentiel borné puis lettre morte.
    # Tentatives avant mise en lettre morte (la 1re publication comprise).
    outbox_max_attempts: int = Field(default=8, ge=1, le=100)
    # Délai de base du backoff : délai après le 1er échec.
    outbox_retry_base_seconds: float = Field(default=2.0, ge=0.1, le=3600.0)
    # Plafond du backoff — borne l'attente, un incident long ne repousse pas
    # la reprise à l'infini.
    outbox_retry_max_seconds: float = Field(default=300.0, ge=1.0, le=86400.0)
    # Amplitude du bruit aléatoire, en fraction du délai calculé (0 = aucun).
    # Évite que N workers rejouent le même lot à la même milliseconde.
    outbox_retry_jitter_ratio: float = Field(default=0.2, ge=0.0, le=1.0)
    # WebSocket (ADR-007)
    ws_max_connections: int = 1000
    ws_heartbeat_interval: int = 30  # secondes
    ws_allowed_origins: list[str] = ["*"]  # CORS WS — restreindre en prod

    # Object Storage (ADR-006)
    object_storage_local_path: str = "./data/assets"
    object_storage_s3_endpoint: str | None = None
    object_storage_s3_bucket: str = "gsie-assets"

    # Auth — JWT RS256 (DEC-000019)
    jwt_algorithm: Literal["RS256"] = "RS256"
    jwt_issuer: str = "gsie-api"
    jwt_audience: str = "gsie-clients"
    jwt_access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    # Dev login — jamais en production ; credentials via variables d'environnement.
    # Désactivé par défaut : un déploiement sans GSIE_ENVIRONMENT=production
    # active le dev login si ce défaut est True — dangereux.
    auth_dev_login_enabled: bool = False
    auth_dev_username: str = "admin"
    auth_dev_password: str = ""

    # Moteur Climate — portail API Météo-France (clé de compte, hors préfixe GSIE_)
    meteofrance_api_key: str | None = Field(default=None, validation_alias="METEOFRANCE_API_KEY")

    # Moteur Botanical — API PlantNet (identification par image, 78 810 espèces)
    # https://my.plantnet.org/ — clé hors préfixe GSIE_ (convention PlantNet)
    plantnet_api_key: str | None = Field(default=None, validation_alias="PLANTNET_API_KEY")

    # Moteur Evidence
    require_rust_backend: bool = False
    evidence_experimental_conflicts_enabled: bool = False

    # Moteur Simulation — valeurs par défaut du modèle linéaire v1.
    # Ces valeurs sont des placeholders documentés : une future version
    # les récupérera du diagnostic source et du Forest Dynamics Engine.
    # Configurables pour calibrer sans redéployer le code.
    simulation_biomasse_initiale: float = Field(default=100.0, ge=0.0)
    simulation_taux_accroissement: float = Field(default=0.02, ge=0.0, le=1.0)

    # Observabilité — OpenTelemetry (DEC-000019)
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "gsie-api"

    @property
    def url_de_migration(self) -> str:
        """URL employée par Alembic — le compte d'administration, pas l'API."""
        return self.migration_database_url or self.database_url

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Valide que la configuration est sûre en production et staging."""
        # Cohérence pool vs max_connections (toujours vérifié, pas seulement en prod)
        max_app_connections = self.gunicorn_workers * (self.db_pool_size + self.db_max_overflow)
        # +1 pour outbox-worker, +5 reserve admin
        if max_app_connections + 6 > self.db_max_connections:
            raise ValueError(
                f"Pool sizing incoherent: {self.gunicorn_workers} workers × "
                f"{self.db_pool_size + self.db_max_overflow} connexions = "
                f"{max_app_connections} + 6 reserve > max_connections={self.db_max_connections}"
            )
        # Contrôle valable partout : le dev login ouvre un compte `admin`.
        if (
            self.auth_dev_login_enabled
            and self.auth_dev_password.strip().lower() in _MOTS_DE_PASSE_DE_REMPLISSAGE
        ):
            raise ValueError(
                "GSIE_AUTH_DEV_PASSWORD porte une valeur de remplissage. Le dev "
                "login accorde le role `admin` : choisissez un mot de passe reel, "
                "ou posez GSIE_AUTH_DEV_LOGIN_ENABLED=false."
            )
        if self.environment in ("production", "staging"):
            if self.debug:
                raise ValueError("debug must be False in production")
            if "gsie_dev" in self.database_url:
                raise ValueError("Default database password not allowed in production")
            utilisateur = urlparse(self.database_url).username or ""
            if utilisateur in _ROLES_PROPRIETAIRES:
                raise ValueError(
                    f"Le role de connexion « {utilisateur} » est proprietaire de la base. "
                    "Un proprietaire PostgreSQL conserve des droits implicites que "
                    "`REVOKE` n'ote pas : l'isolement de `gsie_rgpd_identites` "
                    "(20260728_0011) ne s'applique pas a lui, et l'application lirait "
                    "le mecanisme de reversion du pseudonymat. Connectez-vous avec un "
                    "role membre de `gsie_application`, cree par la migration."
                )
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origin not allowed in production")
            if any("localhost" in o for o in self.cors_origins):
                raise ValueError("localhost CORS origins not allowed in production")
            redis_password = urlparse(self.redis_url).password
            if not redis_password:
                raise ValueError("Redis without password not allowed in production")
            if self.rate_limit_storage_url == "memory://":
                raise ValueError("Distributed rate-limit storage required in production")
            if self.refresh_token_storage_url == "memory://":
                raise ValueError("Distributed refresh-token storage required in production")
            if self.auth_dev_login_enabled:
                raise ValueError("Development login must be disabled in production")
            if not self.require_rust_backend:
                raise ValueError("Rust Evidence backend must be required in production")
            if "*" in self.ws_allowed_origins:
                raise ValueError("Wildcard WebSocket origins not allowed in production")
            if self.db_ssl_mode not in ("require", "verify-ca", "verify-full"):
                raise ValueError(
                    "TLS PostgreSQL requis en production/staging "
                    "(db_ssl_mode doit être 'require', 'verify-ca' ou 'verify-full')"
                )
        return self


# --- Chiffrement .env (audit sécurité P1-1) -------------------------------
# La clé Fernet est stockée hors du repo (~/.config/gsie/env.key).
# Si .env n'existe pas mais .env.enc oui, on déchiffre en mémoire et on
# passe les valeurs à pydantic-settings via un fichier temporaire éphémère
# — on n'injecte JAMAIS dans os.environ, car cela exposerait les secrets à
# tout sous-processus (via /proc/self/environ sur Linux, héritage par défaut).
_KEY_DIR = Path.home() / ".config" / "gsie"
_KEY_FILE = _KEY_DIR / "env.key"
# Résolution robuste : remonte depuis src/gsie_api/core/config.py vers la
# racine de l'API. Quatre .parent correspondent à :
#   config.py → core/ → gsie_api/ → src/ → API root.
# On utilise une garde pour vérifier qu'on tombe bien sur pyproject.toml.
_API_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if not (_API_ROOT / "pyproject.toml").exists():
    # Le module a été déplacé — on ne peut pas deviner la racine, on désactive
    # le déchiffrement (get_settings() lèvera des erreurs métier explicites).
    _API_ROOT = Path(__file__).resolve().parent  # fallback inoffensif
_ENV_FILE = _API_ROOT / ".env"
_ENV_ENC_FILE = _API_ROOT / ".env.enc"

# Cache du contenu déchiffré (en mémoire, jamais écrit sur disque).
_decrypted_env_cache: dict[str, str] | None = None


def _parse_env_line(line: str) -> tuple[str, str] | None:
    """Parse une ligne KEY=VALUE du fichier .env, en gérant les guillemets.

    Retourne None pour les lignes vides ou les commentaires. Retire les
    guillemets entourant la valeur, comme le parseur dotenv de pydantic :
    ``KEY="value"`` → ``value``, ``KEY='value'`` → ``value``.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip()
    # Retire les guillemets entourants (simple ou double), comme dotenv.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    if not key:
        return None
    return key, value


def _load_encrypted_env() -> None:
    """Déchiffre .env.enc en mémoire si .env est absent.

    Idempotent : ne fait rien si .env existe déjà ou si .env.enc est absent.
    Le contenu déchiffré est stocké dans ``_decrypted_env_cache`` (en mémoire,
    jamais sur disque) et injecté via ``_env_settings`` dans pydantic-settings.

    Si la clé Fernet est absente, journalise un warning explicite — ne laisse
    pas pydantic lever une erreur de validation opaque qui ne mentionne pas
    la vraie cause (cf. motif « panne diagnostiquée à côté » corrigé ailleurs
    dans ce dépôt).
    """
    global _decrypted_env_cache

    if _decrypted_env_cache is not None:
        return  # déjà chargé
    if _ENV_FILE.exists() or not _ENV_ENC_FILE.exists():
        return  # .env présent ou .env.enc absent — rien à faire

    if not _KEY_FILE.exists():
        # Warning explicite — ne laisse pas pydantic lever une erreur opaque.
        # En production, ce warning doit être repéré dans les journaux.
        # structlog n'est pas encore configuré à ce stade (avant get_settings),
        # on utilise logging standard avec un message formaté.
        import logging

        logging.getLogger("gsie_api.config").warning(
            "env_enc_key_absente — .env.enc présent mais clé Fernet absente "
            "(key_file=%s, env_enc=%s). L'application ne pourra pas charger "
            "ses secrets — get_settings() lèvera une erreur de validation.",
            str(_KEY_FILE),
            str(_ENV_ENC_FILE),
        )
        return

    from cryptography.fernet import Fernet

    fernet = Fernet(_KEY_FILE.read_bytes())
    plaintext = fernet.decrypt(_ENV_ENC_FILE.read_bytes()).decode("utf-8")

    env_dict: dict[str, str] = {}
    for ligne in plaintext.splitlines():
        parsed = _parse_env_line(ligne)
        if parsed is not None:
            key, value = parsed
            # N'écrase pas une variable déjà positionnée par l'environnement
            # réel (priorité : env réel > .env.enc).
            if key not in os.environ:
                env_dict[key] = value

    _decrypted_env_cache = env_dict


@lru_cache
def get_settings() -> Settings:
    """Retourne un singleton Settings (cache pour éviter les relectures .env)."""
    _load_encrypted_env()
    return Settings()
