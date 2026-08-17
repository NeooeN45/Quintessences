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
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
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
        # Masque les valeurs liées dans les logs SQL et les messages d'erreur.
        # Cela protège notamment mots de passe, jetons et données personnelles.
        "hide_parameters": True,
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
    organisation_id: str | None = None,
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
    dialect_name = session.bind.dialect.name if session.bind is not None else ""
    if dialect_name == "sqlite":
        session.info["user_id"] = user_id
        session.info["roles"] = roles
        session.info["organisation_id"] = organisation_id
        session.info["workspace_id"] = workspace_id
        return

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
    if organisation_id:
        await session.execute(
            text("SELECT set_config('app.current_organisation_id', :oid, true)"),
            {"oid": organisation_id},
        )
    session.info["organisation_id"] = organisation_id
    session.info["workspace_id"] = workspace_id


async def _resolve_active_organisation(
    session: AsyncSession,
    user_id: str,
    request: Request,
) -> str | None:
    """Résout le contexte d'organisation explicite ou unique du compte.

    Un ``user_id`` non-UUID (ex. token de test avec un username comme subject)
    ne peut correspondre à aucune organisation en base — on court-circuite
    l'auto-résolution (sans header) pour éviter une erreur de typage asyncpg
    sur les colonnes UUID. La validation du header ``X-Organisation-Id``
    reste appliquée dans tous les cas.
    """
    requested = request.headers.get("X-Organisation-Id")
    if requested:
        try:
            organisation_id = UUID(requested)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Organisation-Id invalide",
            ) from None
        exists = await session.scalar(
            text(
                "SELECT 1 FROM gsie_organisations.organisation_member "
                "WHERE organisation_id = :oid AND account_id = :uid "
                "AND revoked_at IS NULL"
            ),
            {"oid": str(organisation_id), "uid": user_id},
        )
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte non membre de cette organisation",
            )
        return str(organisation_id)

    # Un user_id non-UUID (ex. token de test) ne peut avoir d'organisation
    # en base — on évite la requête SQL qui échouerait sur le cast UUID.
    try:
        UUID(user_id)
    except (ValueError, TypeError):
        return None

    rows = (
        (
            await session.execute(
                text(
                    "SELECT id FROM gsie_organisations.organisation "
                    "WHERE created_by = :uid OR id IN ("
                    "SELECT organisation_id FROM gsie_organisations.organisation_member "
                    "WHERE account_id = :uid AND revoked_at IS NULL) "
                    "ORDER BY created_at LIMIT 2"
                ),
                {"uid": user_id},
            )
        )
        .scalars()
        .all()
    )
    if len(rows) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contexte organisation requis via X-Organisation-Id",
        )
    return str(rows[0]) if rows else None


async def _resolve_active_workspace(
    session: AsyncSession,
    organisation_id: str | None,
    request: Request,
    token_workspace_id: object,
) -> str | None:
    """Valide le workspace demandé dans l'organisation active."""
    requested = request.headers.get("X-Workspace-Id")
    candidate = requested or (str(token_workspace_id) if token_workspace_id else None)
    if candidate is None or organisation_id is None:
        return None
    try:
        workspace_id = UUID(candidate)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id invalide",
        ) from None
    exists = await session.scalar(
        text(
            "SELECT 1 FROM gsie_organisations.workspace "
            "WHERE id = :wid AND organisation_id = :oid AND deleted_at IS NULL"
        ),
        {"wid": str(workspace_id), "oid": organisation_id},
    )
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace inexistant dans cette organisation",
        )
    return str(workspace_id)


# Type alias pour l'annotation Annotated dans les routers
CurrentUser = dict[str, Any]


async def get_db_user_rls(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncGenerator[AsyncSession, None]:
    """Session RLS limitée au compte, sans sélection d'organisation."""
    async with async_session_factory() as session, session.begin():
        user_id = str(user.get("sub", ""))
        roles = ",".join(user.get("roles", []))
        await set_rls_context(
            session,
            user_id,
            roles,
            workspace_id=str(user["workspace_id"]) if user.get("workspace_id") else None,
        )
        yield session


async def get_db_resource(
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[AsyncSession, None]:
    """Session ressource avec contexte organisation/workspace et DB injectable."""
    user_id = str(user.get("sub", ""))
    roles = ",".join(user.get("roles", []))
    token_workspace_id = user.get("workspace_id")
    await set_rls_context(session, user_id, roles)
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        organisation_id = await _resolve_active_organisation(session, user_id, request)
        workspace_id = await _resolve_active_workspace(
            session,
            organisation_id,
            request,
            token_workspace_id,
        )
    else:
        organisation_id = request.headers.get("X-Organisation-Id")
        workspace_id = request.headers.get("X-Workspace-Id") or (
            str(token_workspace_id) if token_workspace_id else None
        )
    if organisation_id:
        await set_rls_context(
            session,
            user_id,
            roles,
            workspace_id=workspace_id,
            organisation_id=organisation_id,
        )
    yield session


async def get_db_rls(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncGenerator[AsyncSession, None]:
    """Session RLS par compte, compatible avec les endpoints historiques."""
    async with async_session_factory() as session, session.begin():
        user_id = str(user.get("sub", ""))
        roles = ",".join(user.get("roles", []))
        await set_rls_context(
            session,
            user_id,
            roles,
            workspace_id=str(user["workspace_id"]) if user.get("workspace_id") else None,
        )
        yield session
