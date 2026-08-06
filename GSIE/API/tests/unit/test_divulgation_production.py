"""La posture de divulgation en production est verrouillée.

L'application prend délibérément quatre mesures pour ne pas se décrire à un
visiteur non authentifié — `app.py` les cite explicitement comme OWASP A05 :

* documentation interactive coupée (`/docs`, `/redoc`) ;
* schéma OpenAPI non servi ;
* en-tête `Server` retiré des réponses ;
* version PostGIS masquée dans `/ready` (déjà couvert par `test_health.py`).

Aucune des trois premières n'était testée. Les retirer n'aurait fait tomber
aucun test : le schéma OpenAPI complet — tous les chemins, tous les modèles,
tous les champs — serait redevenu public en production sans que rien ne le
signale. Un choix de sécurité que rien ne surveille n'est pas un choix, c'est
une coïncidence.

Ce module ne juge pas la posture, il la constate et l'ancre. Ce qui reste du
ressort du déploiement — restreindre `/metrics` et l'accès réseau aux sondes —
n'est pas testé ici : ces contrôles n'appartiennent pas au code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.core.config import Settings

if TYPE_CHECKING:
    from collections.abc import Iterator


def _kwargs_production(**overrides: object) -> dict[str, object]:
    """Configuration de production valide, reprise de `test_config.py`."""
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
        "transactional_email_mode": "smtp",
        "smtp_host": "smtp.example.com",
        "require_rust_backend": True,
        "db_ssl_mode": "require",
        "mfa_encryption_key": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
    } | overrides


# Mocks du lifespan appliqués à tous les tests de ce module.
# Sans eux, le lifespan crée de vraies connexions DB (asyncpg) et Redis
# qui, au shutdown du TestClient, ferment l'event loop sur Windows et
# polluent les tests suivants (RuntimeError: Event loop is closed).
_LIFESPAN_PATCHES = (
    patch("gsie_api.infrastructure.database.engine"),
    patch("gsie_api.infrastructure.database.async_session_factory"),
    patch(
        "gsie_api.infrastructure.db_privileges" ".verifier_privileges_de_connexion",
        new_callable=AsyncMock,
    ),
    patch(
        "gsie_api.websocket.manager.manager.start_redis_subscriber",
        new_callable=AsyncMock,
    ),
    patch(
        "gsie_api.websocket.manager.manager.start_heartbeat",
        new_callable=AsyncMock,
    ),
    patch(
        "gsie_api.websocket.manager.manager.shutdown",
        new_callable=AsyncMock,
    ),
    patch(
        "gsie_api.auth.refresh_tokens.close_refresh_token_store",
        new_callable=AsyncMock,
    ),
    patch("gsie_api.infrastructure.redis_client.redis_pool"),
)


@pytest.fixture
def app_production(monkeypatch: pytest.MonkeyPatch) -> Iterator[object]:
    """Application construite avec une configuration de production.

    Les mocks du lifespan sont actifs pendant la durée de la fixture pour
    éviter que le TestClient ne crée de vraies connexions DB/Redis.
    """
    reglages = Settings(**_kwargs_production())  # type: ignore[arg-type]
    monkeypatch.setattr("gsie_api.app._settings", reglages)
    for p in _LIFESPAN_PATCHES:
        p.start()
    try:
        yield create_app()
    finally:
        for p in _LIFESPAN_PATCHES:
            p.stop()


@pytest.fixture
def app_developpement(monkeypatch: pytest.MonkeyPatch) -> Iterator[object]:
    """Application construite en développement — la comparaison utile."""
    reglages = Settings(
        **_kwargs_production(
            environment="development",
            require_rust_backend=False,
            db_ssl_mode="prefer",
        )  # type: ignore[arg-type]
    )
    monkeypatch.setattr("gsie_api.app._settings", reglages)
    for p in _LIFESPAN_PATCHES:
        p.start()
    try:
        yield create_app()
    finally:
        for p in _LIFESPAN_PATCHES:
            p.stop()


@pytest.mark.parametrize("chemin", ["/docs", "/redoc"])
def test_la_documentation_interactive_est_coupee_en_production(app_production, chemin) -> None:
    """`/docs` et `/redoc` ne répondent pas en production (OWASP A05)."""
    with TestClient(app_production) as client:
        reponse = client.get(chemin)

    assert reponse.status_code == 404, (
        f"{chemin} répond {reponse.status_code} en production — la "
        "documentation interactive décrit toute la surface de l'API"
    )


def test_le_schema_openapi_n_est_pas_servi_en_production(app_production) -> None:
    """Le schéma OpenAPI n'est pas public en production.

    Plus consequent que `/docs` : le schéma énumère chaque chemin, chaque
    modèle et chaque champ, dans un format directement exploitable par un
    outil. C'est exactement ce que le gestionnaire 404 personnalisé de
    `app.py` s'applique à ne pas divulguer.
    """
    with TestClient(app_production) as client:
        reponses = [client.get(chemin) for chemin in ("/openapi.json", "/api/v1/openapi.json")]

    for reponse in reponses:
        assert reponse.status_code == 404, (
            f"{reponse.request.url.path} répond {reponse.status_code} en "
            "production — la surface complète de l'API est publique"
        )


def test_la_documentation_reste_disponible_en_developpement(app_developpement) -> None:
    """En développement, la documentation répond.

    Sans ce contrôle, couper la documentation en toutes circonstances ferait
    passer les tests précédents — et priverait le développement d'un outil
    utile. Ce qui est verrouillé, c'est la **distinction**, pas l'absence.
    """
    with TestClient(app_developpement) as client:
        reponse = client.get("/docs")

    assert reponse.status_code == 200


def test_l_entete_server_est_retire(app_production) -> None:
    """Aucune réponse ne porte l'en-tête `Server` (empreinte du serveur)."""
    with TestClient(app_production) as client:
        reponse = client.get("/health")

    assert "server" not in {
        cle.lower() for cle in reponse.headers
    }, f"en-tête Server présent : {reponse.headers.get('server')!r}"
