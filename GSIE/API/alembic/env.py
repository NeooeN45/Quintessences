"""Alembic env — configuration async pour PostgreSQL.

Utilise asyncpg (SQLAlchemy 2.0 async) pour les migrations.
Importe le registre v6.2 pour que l'autogénération détecte uniquement le
schéma courant. Les modèles v6.1 archivés utilisent une base distincte et
ne doivent jamais réapparaître dans une migration.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from gsie_api.core.config import get_settings
from gsie_api.infrastructure.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.database_url)
_EXTENSION_TABLES = frozenset({"spatial_ref_sys"})
# Index automatiquement reflétés par GeoAlchemy2 sur les colonnes Geometry
# générées (Computed) — l'index explicite idx_place_geom_4326 est créé par
# la migration 20260727_0005 et déclaré dans __table_args__. L'index
# ix_place_geom_4326 est un artefact de réflexion GeoAlchemy2 à ignorer.
_GA2_REFLECTED_INDEXES = frozenset({"ix_place_geom_4326"})


def include_object(
    object_: object,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: object,
) -> bool:
    """Ignore les objets possédés par PostGIS et les index reflétés GeoAlchemy2."""
    del object_, reflected, compare_to
    if type_ == "table" and name in _EXTENSION_TABLES:
        return False
    if type_ == "index" and name in _GA2_REFLECTED_INDEXES:
        return False
    return True


def _normalize_default(value: object) -> str:
    """Normalise un server_default pour la comparaison.

    PostgreSQL stocke `now()` et `CURRENT_TIMESTAMP` de manière équivalente ;
    SQLAlchemy exprime `func.now()` comme une fonction et `text("now()")` comme
    du texte. On normalise tout vers une chaîne canonique pour éviter les
    faux positifs de dérive.
    """
    text = str(value).strip().lower().replace("(", "").replace(")", "")
    return text.replace("current_timestamp", "now").replace("::", " ")


def compare_server_default(
    context: object,
    inspected_column: object,
    metadata_column: object,
    inspected_default: object,
    metadata_default: object,
    rendered_metadata_default: object,
) -> bool | None:
    """Compare deux server_default en normalisant les équivalences temporelles.

    Retourne False (équivalents) pour now()/CURRENT_TIMESTAMP/func.now(),
    None sinon pour laisser Alembic appliquer sa comparaison standard.
    """
    del context, inspected_column, metadata_column
    if inspected_default is None and metadata_default is None:
        return None
    if inspected_default is None or metadata_default is None:
        return None
    inspected_norm = _normalize_default(inspected_default)
    # metadata_default peut être un objet func.now() ; rendered_metadata_default
    # est sa version rendue en SQL (ex. "now()") — plus fiable pour comparer.
    metadata_value = rendered_metadata_default if rendered_metadata_default is not None else metadata_default
    metadata_norm = _normalize_default(metadata_value)
    if inspected_norm == metadata_norm:
        return False
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        compare_type=True,
        compare_server_default=compare_server_default,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=compare_server_default,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
