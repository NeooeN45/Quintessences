"""Fixtures partagées — base PostgreSQL/PostGIS réelle via testcontainers.

Centralise ce qui était dupliqué dans tests/integration/test_database.py,
pour que les autres suites (Knowledge Engine, pipeline) puissent réutiliser
la même base de test sans relancer un conteneur Docker par fichier.
"""

import asyncio
import os

# Rate limiter en memory:// pour les tests — AVANT tout import gsie_api.
#
# Le limiter production utilise Redis (DB 1) partagé entre workers Gunicorn.
# En test xdist (-n 2), ce Redis est partagé entre les workers pytest : un
# worker peut épuiser le quota d'un endpoint avant qu'un autre worker
# n'arrive, produisant des 429 fallacieux. ``memory://`` donne un compteur
# par processus Python — chaque worker xdist a le sien, isolé des autres.
#
# Cette variable d'environnement doit être set AVANT l'import de
# ``gsie_api.core.limiter`` (qui crée le singleton Limiter au moment de
# l'import). pydantic-settings priorise les env vars sur le .env file,
# donc ``GSIE_RATE_LIMIT_STORAGE_URL=memory://`` surcharge la valeur Redis
# du .env local. Le comportement du limiter (comptage, 429) est identique
# avec memory storage ; seul le partage cross-worker disparaît.
os.environ.setdefault("GSIE_RATE_LIMIT_STORAGE_URL", "memory://")
# Refresh token store en memory:// pour les tests unitaires — AVANT tout
# import gsie_api. Sans cette surcharge, get_refresh_token_store() crée un
# RedisRefreshTokenStore qui tente de se connecter à localhost:6379, et les
# 6 tests auth qui utilisent les refresh tokens échouent avec ConnectionError.
# memory:// utilise MemoryRefreshTokenStore (dict en mémoire), équivalent
# fonctionnel pour les tests unitaires.
os.environ.setdefault("GSIE_REFRESH_TOKEN_STORAGE_URL", "memory://")

from collections.abc import AsyncGenerator, Iterator, Sequence
from contextlib import ExitStack
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gsie_api.infrastructure.models import Base

# Cibles du lifespan qui créent de vraies connexions (asyncpg, WebSocket).
# Sans les mocker, ``TestClient(app)`` déclenche le lifespan qui ouvre/firme des
# connexions async, fermant l'event loop sur Windows et polluant les tests
# suivants (RuntimeError: Event loop is closed).
# Note : ``close_refresh_token_store`` n'est PAS mocké ici — le mock laisse la
# connexion Redis orpheline, qui réapparaît sur l'event loop fermée au test
# suivant. La fermeture propre est gérée par le fixture ``_ensure_fresh_event_loop``.
_LIFESPAN_MOCK_TARGETS = (
    "gsie_api.infrastructure.database.async_session_factory",
    "gsie_api.infrastructure.db_privileges.verifier_privileges_de_connexion",
    "gsie_api.websocket.manager.manager.start_redis_subscriber",
    "gsie_api.websocket.manager.manager.start_heartbeat",
    "gsie_api.websocket.manager.manager.shutdown",
)


@pytest.fixture
def mock_lifespan() -> Iterator[ExitStack]:
    """Mocke les cibles async du lifespan pour éviter les connexions réelles.

    Utiliser ce fixture dans tout test unitaire qui crée un ``TestClient(app)``
    avec le lifespan context manager. Les tests d'intégration qui nécessitent
    de vraies connexions DB/Redis ne l'utilisent pas.
    """
    with ExitStack() as stack:
        for target in _LIFESPAN_MOCK_TARGETS:
            stack.enter_context(patch(target, new_callable=AsyncMock))
        yield stack


@pytest.fixture(autouse=True)
def _ensure_fresh_event_loop() -> object:
    """Garantit une event loop non fermée pour chaque test.

    Sur Windows, pytest-asyncio (mode auto, scope function) ferme l'event
    loop après chaque test async mais ne la remet pas à ``None``. Les tests
    synchrones utilisant ``TestClient`` (qui appelle ``asyncio.get_event_loop()``
    en interne via httpx) récupèrent alors une loop fermée et lèvent
    ``RuntimeError: Event loop is closed``.

    Cette fixture autouse s'exécute avant chaque test : si la loop courante
    est fermée, on en crée une nouvelle. Pour les tests async, pytest-asyncio
    crée sa propre loop (qui remplace celle-ci). Le coût est négligeable
    (un test ``is_closed()`` par test).
    """
    try:
        # Python 3.12+ : get_event_loop() est déprécié quand aucune loop
        # n'est en cours. On utilise get_running_loop() (non déprécié) qui
        # lève RuntimeError s'il n'y a pas de loop — dans ce cas, on en crée
        # une nouvelle. On n'appelle jamais get_event_loop() ni
        # get_event_loop_policy().get_event_loop() (les deux dépréciés).
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Pas de loop en cours — en créer une pour TestClient.
            asyncio.set_event_loop(asyncio.new_event_loop())
        else:
            if loop.is_closed():
                asyncio.set_event_loop(asyncio.new_event_loop())
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> object:
    """Réinitialise les compteurs du rate limiter (slowapi) avant chaque test.

    Le ``Limiter`` est un singleton module-level (``core/limiter.py``) partagé
    par toutes les instances d'app créées via ``create_app()``. Sans reset,
    les compteurs s'accumulent entre tests dans le même worker xdist et les
    tests E2E reçoivent un ``429 Too Many Requests`` fallacieux.

    ``limiter.reset()`` vide le storage (Redis ou memory). Les tests qui
    vérifient explicitement le comportement du rate limiter
    (``test_rate_limit_bulk.py``, ``test_limiter_contrat.py``) utilisent
    leur propre limiter mocké et ne sont pas affectés.
    """
    from gsie_api.core.limiter import limiter

    limiter.reset()
    yield


# Fichiers dont les tests partagent un état global (DB PostgreSQL, singleton
# de métriques, quota Redis) et ne doivent pas tourner en parallèle sur
# plusieurs workers xdist. On ne modifie pas le fichier de test lui-même :
# le marquage se fait ici, à la collecte.
#
# Le groupe xdist porte un nom générique — ces fichiers couvrent l'outbox,
# l'orchestration, les index Treekipedia et les métriques DB, pas seulement
# la concurrence outbox. Le nom ancien `outbox_concurrence` décrivait mal le
# contenu et grandissait au fil des ajouts.
_FICHIERS_SERIAL = (
    "test_outbox_concurrence.py",
    "test_e2e_cross_engines.py",  # TestRateLimiting — 35 req consécutives
    "test_e2e_api.py",  # TestCorrelationComputeE2E — état DB partagé
    "test_orchestration.py",  # Chaîne complète — état DB partagé
    "test_pipeline_api.py",  # Pipeline complet — état DB partagé
    "test_resources_api_validation.py",  # Révisions + outbox — état DB partagé
    "test_recommendation_diagnostic.py",  # Diagnostic → recommandation — état DB partagé
    "test_db_quality_metrics.py",  # Patch collect_db_metrics — singleton partagé
    "test_treekipedia_performance.py",  # Index lookup — état DB partagé
    "test_restauration_db.py",  # Backup/restore — conteneur dédié, pas en parallèle
)
_XDIST_SERIAL_GROUP = "shared_state_serial"


def pytest_collection_modifyitems(items: Sequence[Any]) -> None:
    """Marque `serial` et regroupe sur un seul worker xdist les tests listés
    dans `_FICHIERS_SERIAL`, afin qu'ils ne soient jamais répartis sur des
    workers différents ni exécutés concurremment entre eux."""
    for item in items:
        if item.fspath.basename in _FICHIERS_SERIAL:
            item.add_marker(pytest.mark.serial)
            item.add_marker(pytest.mark.xdist_group(name=_XDIST_SERIAL_GROUP))


def _docker_available(tentatives: int = 3, pause: float = 2.0) -> bool:
    """Vérifie si Docker est disponible sans lever d'exception.

    Réessaie, parce que la sonde est faillible sous charge : `docker.from_env()`
    a échoué alors que `docker ps` répondait sur la même machine, et les
    47 tests d'isolement RGPD ont été sautés en silence — la suite affichant
    « 210 passés » sans avoir vérifié une seule garantie de la base. Un test de
    sécurité qui ne s'exécute pas se distingue mal d'un test qui passe.

    Une seule tentative suffit quand Docker est réellement absent : la connexion
    est refusée immédiatement et les reprises n'ajoutent que quelques secondes,
    payées une fois par session.
    """
    import time

    for restantes in range(tentatives - 1, -1, -1):
        try:
            import docker

            docker.from_env().version()
            return True
        except Exception:
            if restantes:
                time.sleep(pause)
    return False


DOCKER_AVAILABLE = _docker_available()

# Filet pour l'intégration continue : là où Docker est censé être présent, une
# sonde en échec doit arrêter la suite, pas la vider de ses tests. Sur un poste
# de développement sans Docker, la variable reste absente et le saut demeure —
# on ne bloque personne pour un outil qu'il n'a pas.
if not DOCKER_AVAILABLE and os.environ.get("GSIE_REQUIRE_DOCKER") == "1":
    raise RuntimeError(
        "GSIE_REQUIRE_DOCKER=1 mais Docker est injoignable : les tests "
        "d'intégration seraient sautés et la suite passerait au vert sans "
        "avoir rien vérifié."
    )

requires_docker = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker is not available (testcontainers requires Docker)",
)


@pytest.fixture(scope="session")
def postgres_url() -> AsyncGenerator[str, None]:
    """Lance un conteneur PostgreSQL/PostGIS/pgvector (une fois par session).

    Utilise l'image locale `gsie-testdb:latest` si elle existe (construite
    via `docker build -t gsie-testdb:latest -f tests/Dockerfile.testdb .`),
    ce qui évite l'apt-get à chaque session (~15s économisés). Sinon,
    fallback sur l'image officielle `postgis/postgis:16-3.4` avec
    installation de pgvector à la volée.

    L'installation dépend du réseau : sans elle, `CREATE EXTENSION vector`
    échoue plus loin, dans `db_session`, sur un message qui ne dit pas que
    la cause est un apt muet. On vérifie donc le code de sortie ici et on
    remonte la sortie d'apt telle quelle — un diagnostic à sa cause coûte
    moins cher qu'un diagnostic à trois fixtures de distance.
    """
    import docker as _docker
    from testcontainers.postgres import PostgresContainer

    # Détection de l'image locale pré-construite (pgvector déjà installé).
    _image_local = "gsie-testdb:latest"
    _use_local = False
    try:
        client = _docker.from_env()
        client.images.get(_image_local)
        _use_local = True
    except Exception:
        pass  # Image absente — fallback sur l'image officielle

    image = _image_local if _use_local else "postgis/postgis:16-3.4"

    with PostgresContainer(
        image=image,
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_test",
    ) as postgres:
        if not _use_local:
            # Installer pgvector dans le conteneur (le dépôt PGDG est présent).
            container = postgres.get_wrapped_container()
            code, sorties = container.exec_run(
                ["sh", "-c", "apt-get update -qq && apt-get install -y -qq postgresql-16-pgvector"],
                demux=True,
            )
            if code != 0:
                # `demux=True` renvoie le couple (stdout, stderr), chacun pouvant
                # être None si le flux est resté vide.
                flux = b"\n".join(f for f in (sorties or (None, None)) if f)
                raise RuntimeError(
                    "Installation de pgvector échouée dans le conteneur de test "
                    f"(code {code}). Vérifier l'accès réseau au dépôt PGDG.\n"
                    f"{flux.decode('utf-8', errors='replace')}"
                )
        yield postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")


@pytest.fixture
async def db_session(postgres_url: str) -> AsyncGenerator[AsyncSession, None]:
    """Session DB sur PostgreSQL/PostGIS réel — schéma créé puis nettoyé par test."""
    engine = create_async_engine(postgres_url, pool_pre_ping=True)

    # postgis_tiger_geocoder (activé par défaut sur l'image postgis/postgis) crée
    # une table `place` qui entre en conflit avec notre PlaceModel.
    # pgvector est installé à la volée dans le fixture postgres_url (ci-dessus).
    async with engine.begin() as conn:
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE"))
        await conn.execute(text("DROP EXTENSION IF EXISTS postgis_topology CASCADE"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # `create_all` ne cree pas les schemas : depuis `20260728_0011`, les donnees
    # personnelles vivent hors de `public` et leurs tables echoueraient a se
    # creer. On declare donc les schemas que le registre reference.
    async with engine.begin() as conn:
        for schema in sorted(
            {table.schema for table in Base.metadata.tables.values() if table.schema}
        ):
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
