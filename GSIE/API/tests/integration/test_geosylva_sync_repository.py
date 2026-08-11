"""Persistance réelle et cloisonnement des parcelles synchronisées."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from gsie_api.infrastructure.models.accounts import UserAccountModel
from gsie_api.sync.geosylva import (
    GeoSylvaParcelMutation,
    GeoSylvaParcelRecord,
    GeoSylvaSyncConflictError,
    GeoSylvaSyncService,
)
from gsie_api.sync.repository import SqlAlchemyGeoSylvaParcelRepository


async def test_deux_comptes_peuvent_utiliser_le_meme_identifiant_local(
    db_session: AsyncSession,
) -> None:
    account_a = UserAccountModel()
    account_b = UserAccountModel()
    db_session.add_all([account_a, account_b])
    await db_session.flush()
    service = GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(db_session))
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)

    await service.upsert(
        account_a.id,
        "parcelle-locale-1",
        GeoSylvaParcelMutation(uuid4(), None, now, {"name": "Compte A"}),
    )
    await service.upsert(
        account_b.id,
        "parcelle-locale-1",
        GeoSylvaParcelMutation(uuid4(), None, now, {"name": "Compte B"}),
    )

    rows_a, total_a = await service.list(account_a.id, page=1, size=50)
    rows_b, total_b = await service.list(account_b.id, page=1, size=50)

    assert total_a == total_b == 1
    assert rows_a[0].payload["name"] == "Compte A"
    assert rows_b[0].payload["name"] == "Compte B"


async def test_deux_creations_concurrentes_ne_produisent_jamais_une_erreur_sql(
    db_session: AsyncSession,
) -> None:
    account = UserAccountModel()
    db_session.add(account)
    await db_session.commit()
    engine = db_session.bind
    assert isinstance(engine, AsyncEngine)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)

    async def create(name: str) -> GeoSylvaParcelRecord:
        async with sessions() as session, session.begin():
            service = GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(session))
            return await service.upsert(
                account.id,
                "parcelle-concurrente",
                GeoSylvaParcelMutation(uuid4(), None, now, {"name": name}),
            )

    results = await asyncio.gather(create("A"), create("B"), return_exceptions=True)

    assert sum(isinstance(result, GeoSylvaParcelRecord) for result in results) == 1
    assert sum(isinstance(result, GeoSylvaSyncConflictError) for result in results) == 1
