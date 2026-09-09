"""INV-008 — retries offline et reprise après transaction interrompue."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from gsie_api.infrastructure.models.accounts import UserAccountModel
from gsie_api.infrastructure.models.sync import GeoSylvaParcelSyncModel
from gsie_api.sync.geosylva import GeoSylvaParcelMutation, GeoSylvaSyncService
from gsie_api.sync.repository import SqlAlchemyGeoSylvaParcelRepository


@pytest.mark.asyncio
async def test_rejouer_la_meme_operation_ne_duplique_pas_et_n_incremente_pas(
    db_session: AsyncSession,
) -> None:
    account = UserAccountModel()
    db_session.add(account)
    await db_session.flush()

    service = GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(db_session))
    operation_id = uuid4()
    mutation = GeoSylvaParcelMutation(
        operation_id=operation_id,
        base_version=None,
        client_updated_at=datetime(2026, 9, 8, 14, 0, tzinfo=UTC),
        payload={"name": "Saisie terrain offline"},
    )

    premiere = await service.upsert(account.id, "parcelle-retry", mutation)
    rejouee = await service.upsert(account.id, "parcelle-retry", mutation)

    assert premiere.version == 1
    assert rejouee.version == 1
    assert rejouee.last_operation_id == operation_id

    lignes = (
        (
            await db_session.execute(
                select(GeoSylvaParcelSyncModel).where(
                    GeoSylvaParcelSyncModel.account_id == account.id,
                    GeoSylvaParcelSyncModel.client_id == "parcelle-retry",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(lignes) == 1


@pytest.mark.asyncio
async def test_operation_rollbackee_peut_etre_rejouee_sans_perte(
    db_session: AsyncSession,
) -> None:
    account = UserAccountModel()
    db_session.add(account)
    await db_session.commit()
    engine = db_session.bind
    assert isinstance(engine, AsyncEngine)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    operation_id = uuid4()
    mutation = GeoSylvaParcelMutation(
        operation_id=operation_id,
        base_version=None,
        client_updated_at=datetime(2026, 9, 8, 14, 5, tzinfo=UTC),
        payload={"name": "Saisie avant coupure"},
    )

    # Simule une coupure/crash après flush serveur mais avant commit durable.
    async with sessions() as interrompue:
        transaction = await interrompue.begin()
        service = GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(interrompue))
        await service.upsert(account.id, "parcelle-coupure", mutation)
        await transaction.rollback()

    async with sessions() as reprise, reprise.begin():
        service = GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(reprise))
        resultat = await service.upsert(account.id, "parcelle-coupure", mutation)
        assert resultat.version == 1
        assert resultat.last_operation_id == operation_id
        assert resultat.payload["name"] == "Saisie avant coupure"

    async with sessions() as verification:
        lignes = (
            (
                await verification.execute(
                    select(GeoSylvaParcelSyncModel).where(
                        GeoSylvaParcelSyncModel.account_id == account.id,
                        GeoSylvaParcelSyncModel.client_id == "parcelle-coupure",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(lignes) == 1
        assert lignes[0].server_version == 1
        assert lignes[0].last_operation_id == operation_id


@pytest.mark.asyncio
async def test_retry_de_suppression_conserve_un_tombstone_unique(
    db_session: AsyncSession,
) -> None:
    account = UserAccountModel()
    db_session.add(account)
    await db_session.flush()
    service = GeoSylvaSyncService(SqlAlchemyGeoSylvaParcelRepository(db_session))
    now = datetime(2026, 9, 8, 14, 10, tzinfo=UTC)

    cree = await service.upsert(
        account.id,
        "parcelle-delete-retry",
        GeoSylvaParcelMutation(uuid4(), None, now, {"name": "À supprimer"}),
    )
    operation_id = uuid4()

    premiere = await service.delete(
        account.id,
        "parcelle-delete-retry",
        operation_id=operation_id,
        base_version=cree.version,
        client_updated_at=now,
    )
    rejouee = await service.delete(
        account.id,
        "parcelle-delete-retry",
        operation_id=operation_id,
        base_version=cree.version,
        client_updated_at=now,
    )

    assert premiere.version == 2
    assert rejouee.version == 2
    assert rejouee.deleted_at is not None
    assert rejouee.last_operation_id == operation_id

