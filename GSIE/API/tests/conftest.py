"""Fixtures partagées — base PostgreSQL/PostGIS réelle via testcontainers.

Centralise ce qui était dupliqué dans tests/integration/test_database.py,
pour que les autres suites (Knowledge Engine, pipeline) puissent réutiliser
la même base de test sans relancer un conteneur Docker par fichier.
"""

import asyncio
import os
import warnings
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

    ``get_event_loop()`` émet un ``DeprecationWarning`` quand aucune loop
    n'est posée — et c'est justement le cas qu'on interroge. Le filtre est
    local à l'appel : on tait l'avertissement de la sonde, pas ceux du code
    testé. L'API disparaît en 3.14 ; d'ici là, elle reste le seul moyen de
    savoir si la loop courante est fermée sans en créer une au passage.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            loop = asyncio.get_event_loop_policy().get_event_loop()
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


# Fichiers dont les tests dépendent d'un état de concurrence réel (verrous
# PostgreSQL `FOR UPDATE SKIP LOCKED`) ou d'un quota de rate limiter partagé
# sur Redis, et ne doivent jamais tourner en parallèle avec un autre test du
# même fichier. On ne modifie pas le fichier de test lui-même : le marquage
# se fait ici, à la collecte.
_FICHIERS_SERIAL = (
    "test_outbox_concurrence.py",
    "test_e2e_cross_engines.py",  # TestRateLimiting consomme 35 req sur /correlation/compute
)


def pytest_collection_modifyitems(items: Sequence[Any]) -> None:
    """Marque `serial` et regroupe sur un seul worker xdist les tests listés
    dans `_FICHIERS_SERIAL`, afin qu'ils ne soient jamais répartis sur des
    workers différents ni exécutés concurremment entre eux."""
    for item in items:
        if item.fspath.basename in _FICHIERS_SERIAL:
            item.add_marker(pytest.mark.serial)
            item.add_marker(pytest.mark.xdist_group(name="outbox_concurrence"))


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
    """Lance un conteneur PostgreSQL/PostGIS (une fois par session de tests).

    L'image `postgis/postgis:16-3.4` n'inclut pas pgvector. On l'installe
    à la volée via apt (le dépôt PGDG est déjà configuré par l'image de
    base postgres:16) avant de créer l'extension.

    L'installation dépend du réseau : sans elle, `CREATE EXTENSION vector`
    échoue plus loin, dans `db_session`, sur un message qui ne dit pas que
    la cause est un apt muet. On vérifie donc le code de sortie ici et on
    remonte la sortie d'apt telle quelle — un diagnostic à sa cause coûte
    moins cher qu'un diagnostic à trois fixtures de distance.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        driver="asyncpg",
        username="gsie",
        password="gsie_test",
        dbname="gsie_test",
    ) as postgres:
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
