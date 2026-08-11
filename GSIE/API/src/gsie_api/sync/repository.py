"""Dépôt SQLAlchemy des répliques de parcelles GeoSylva."""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.infrastructure.models.sync import GeoSylvaParcelSyncModel
from gsie_api.sync.geosylva import GeoSylvaParcelRecord


class SqlAlchemyGeoSylvaParcelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_update(
        self,
        account_id: UUID,
        client_id: str,
    ) -> GeoSylvaParcelRecord | None:
        # Un verrou de ligne ne protège pas une ligne encore absente. Le verrou
        # transactionnel dérivé de (compte, client) sérialise aussi deux
        # premières créations concurrentes, sans verrou global.
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key": f"{account_id}:{client_id}"},
        )
        statement = (
            select(GeoSylvaParcelSyncModel)
            .where(
                GeoSylvaParcelSyncModel.account_id == account_id,
                GeoSylvaParcelSyncModel.client_id == client_id,
            )
            .with_for_update()
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._record(model) if model is not None else None

    async def save(self, record: GeoSylvaParcelRecord) -> GeoSylvaParcelRecord:
        statement = select(GeoSylvaParcelSyncModel).where(
            GeoSylvaParcelSyncModel.account_id == record.account_id,
            GeoSylvaParcelSyncModel.client_id == record.client_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        if model is None:
            model = GeoSylvaParcelSyncModel(
                account_id=record.account_id,
                client_id=record.client_id,
                payload=record.payload,
                client_updated_at=record.client_updated_at,
                server_version=record.version,
                last_operation_id=record.last_operation_id,
                deleted_at=record.deleted_at,
            )
            self._session.add(model)
        else:
            model.payload = record.payload
            model.client_updated_at = record.client_updated_at
            model.server_version = record.version
            model.last_operation_id = record.last_operation_id
            model.deleted_at = record.deleted_at
        await self._session.flush()
        await self._session.refresh(model)
        return self._record(model)

    async def list_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[GeoSylvaParcelRecord], int]:
        filters = (GeoSylvaParcelSyncModel.account_id == account_id,)
        count = await self._session.scalar(
            select(func.count()).select_from(GeoSylvaParcelSyncModel).where(*filters)
        )
        statement = (
            select(GeoSylvaParcelSyncModel)
            .where(*filters)
            .order_by(GeoSylvaParcelSyncModel.updated_at, GeoSylvaParcelSyncModel.client_id)
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [self._record(model) for model in models], int(count or 0)

    @staticmethod
    def _record(model: GeoSylvaParcelSyncModel) -> GeoSylvaParcelRecord:
        return GeoSylvaParcelRecord(
            account_id=model.account_id,
            client_id=model.client_id,
            payload=dict(model.payload),
            client_updated_at=model.client_updated_at,
            version=model.server_version,
            last_operation_id=model.last_operation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
