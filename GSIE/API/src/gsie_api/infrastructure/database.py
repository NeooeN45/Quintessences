"""Base de données — SQLAlchemy 2.0 async + asyncpg (DEC-000019).

Configuration PgBouncer :
- statement_cache_size=0 côté asyncpg quand db_pgbouncer_mode=True
- Connexion directe dédiée pour LISTEN/NOTIFY (bypass pooler)

Row Level Security (DEC-000037, migration 20260727_0004) :
- ``set_rls_context`` injecte le contexte utilisateur (id + rôles) dans
  la session PostgreSQL via ``SET LOCAL`` avant toute requête sur les
  tables sensibles (consent, data_subject, sensitivity_classification,
  access_policy, sample, observation).
- ``get_db_rls`` est une dependency FastAPI combinant ``get_db`` +
  ``get_current_user`` — à utiliser sur les routers qui touchent les
  tables RLS.
"""

from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gsie_api.core.auth import get_current_user
from gsie_api.core.config import Settings, get_settings

_settings = get_settings()


def _build_engine_kwargs(settings: Settings) -> dict[str, Any]:
    """Construit les kwargs du engine SQLAlchemy selon la configuration.

    Extracted function pour testabilité — PgBouncer mode désactive
    les prepared statements (DEC-000019 ajustement P0).
    """
    kwargs: dict[str, Any] = {
        "echo": settings.db_echo,
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_pre_ping": True,
        "pool_timeout": settings.db_pool_timeout,
        # Recycle les connexions après 30 min — évite les connexions mortes
        # derrière un firewall/load-balancer qui coupe les sockets idle.
        "pool_recycle": 1800,
    }
    connect_args: dict[str, Any] = {}
    if settings.db_pgbouncer_mode:
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0

    # TLS PostgreSQL (audit sécurité 2026-07-27 P0-4). asyncpg accepte les
    # valeurs de sslmode libpq directement via connect_args["ssl"].
    # "disable" est le seul mode explicitement sans chiffrement.
    if settings.db_ssl_mode != "disable":
        connect_args["ssl"] = settings.db_ssl_mode

    if connect_args:
        kwargs["connect_args"] = connect_args
    return kwargs


# Engine principal — mode PgBouncer : désactive prepared statements
_engine_kwargs = _build_engine_kwargs(_settings)

engine = create_async_engine(_settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Requis pour async (global_rules)
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI — fournit une session DB par requête.

    Rollback automatique en cas d'exception (global_rules connection leaks).
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def set_rls_context(
    session: AsyncSession,
    user_id: str,
    roles: str,
    workspace_id: str | None = None,
) -> None:
    """Injecte le contexte RLS dans la session PostgreSQL (DEC-000037).

    Pose ``app.current_user_id`` et ``app.current_user_roles`` via
    ``SET LOCAL`` — valable pour la transaction courante uniquement.
    Si ``workspace_id`` est fourni (claim JWT optionnel), pose aussi
    ``app.current_workspace_id`` pour les futures policies RLS workspace.
    À appeler **après** le début de transaction (premier query ou
    ``session.begin()`` explicite) et **avant** toute requête sur une
    table protégée par RLS.

    Args:
        session: Session SQLAlchemy async.
        user_id: UUID de l'utilisateur authentifié (JWT ``sub``).
        roles: Liste CSV des rôles (ex. ``"admin,researcher"``).
        workspace_id: UUID du workspace courant (JWT ``workspace_id``), optionnel.
    """
    # set_config() est l'équivalent fonctionnel de SET LOCAL et accepte
    # les paramètres liés — SET LOCAL est une commande utility qui ne les
    # accepte pas (audit sécurité 2026-08-01). Le 3e argument `true` rend
    # la configuration locale à la transaction courante.
    await session.execute(
        text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": user_id}
    )
    await session.execute(
        text("SELECT set_config('app.current_user_roles', :roles, true)"), {"roles": roles}
    )
    if workspace_id:
        await session.execute(
            text("SELECT set_config('app.current_workspace_id', :wid, true)"),
            {"wid": workspace_id},
        )


# Type alias pour l'annotation Annotated dans les routers
CurrentUser = dict[str, Any]


async def get_db_rls(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI — session DB avec contexte RLS injecté.

    Combine ``get_db`` + ``get_current_user`` : injecte
    ``app.current_user_id`` et ``app.current_user_roles`` avant de
    fournir la session. À utiliser sur les routers qui touchent les
    tables sensibles (consent, data_subject, sensitivity_classification,
    access_policy, sample, observation).

    Usage ::
        from gsie_api.infrastructure.database import get_db_rls

        @router.get("/consent")
        async def list_consent(session: Annotated[AsyncSession, Depends(get_db_rls)]):
            ...
    """
    # Injection du contexte RLS avant toute requête — SET LOCAL requiert
    # une transaction active. Le bloc ``session.begin()`` garantit le
    # commit en sortie nominale et le rollback en cas d'exception.
    async with async_session_factory() as session, session.begin():
        user_id = str(user.get("sub", ""))
        roles = ",".join(user.get("roles", []))
        workspace_id = user.get("workspace_id")
        await set_rls_context(
            session,
            user_id,
            roles,
            workspace_id=str(workspace_id) if workspace_id else None,
        )
        yield session
