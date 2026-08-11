"""Règles déterministes de synchronisation des parcelles GeoSylva."""

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GeoSylvaParcelMutation:
    """Écriture mobile idempotente fondée sur la version serveur connue."""

    operation_id: UUID
    base_version: int | None
    client_updated_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class GeoSylvaParcelRecord:
    """Instantané serveur appartenant à un seul compte Quintessences."""

    account_id: UUID
    client_id: str
    payload: dict[str, Any]
    client_updated_at: datetime
    version: int
    last_operation_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class GeoSylvaParcelRepository(Protocol):
    async def get_for_update(
        self,
        account_id: UUID,
        client_id: str,
    ) -> GeoSylvaParcelRecord | None: ...

    async def save(self, record: GeoSylvaParcelRecord) -> GeoSylvaParcelRecord: ...

    async def list_for_account(
        self,
        account_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[GeoSylvaParcelRecord], int]: ...


class GeoSylvaSyncConflictError(Exception):
    """La version mobile ne correspond plus à l'instantané serveur."""

    def __init__(self, current: GeoSylvaParcelRecord | None) -> None:
        super().__init__("Conflit de version de synchronisation")
        self.current = current


class GeoSylvaSyncService:
    """Applique les mutations sans écrasement implicite ni mélange de comptes."""

    def __init__(self, repository: GeoSylvaParcelRepository) -> None:
        self._repository = repository

    async def upsert(
        self,
        account_id: UUID,
        client_id: str,
        mutation: GeoSylvaParcelMutation,
    ) -> GeoSylvaParcelRecord:
        current = await self._repository.get_for_update(account_id, client_id)
        if current is not None and current.last_operation_id == mutation.operation_id:
            return current
        if current is None:
            if mutation.base_version is not None:
                raise GeoSylvaSyncConflictError(None)
            now = datetime.now(UTC)
            record = GeoSylvaParcelRecord(
                account_id=account_id,
                client_id=client_id,
                payload=mutation.payload,
                client_updated_at=mutation.client_updated_at,
                version=1,
                last_operation_id=mutation.operation_id,
                created_at=now,
                updated_at=now,
                deleted_at=None,
            )
            return await self._repository.save(record)
        if mutation.base_version != current.version:
            raise GeoSylvaSyncConflictError(current)
        return await self._repository.save(
            replace(
                current,
                payload=mutation.payload,
                client_updated_at=mutation.client_updated_at,
                version=current.version + 1,
                last_operation_id=mutation.operation_id,
                updated_at=datetime.now(UTC),
                deleted_at=None,
            )
        )

    async def delete(
        self,
        account_id: UUID,
        client_id: str,
        *,
        operation_id: UUID,
        base_version: int | None,
        client_updated_at: datetime,
    ) -> GeoSylvaParcelRecord:
        current = await self._repository.get_for_update(account_id, client_id)
        if current is not None and current.last_operation_id == operation_id:
            return current
        now = datetime.now(UTC)
        if current is None:
            if base_version is not None:
                raise GeoSylvaSyncConflictError(None)
            tombstone = GeoSylvaParcelRecord(
                account_id=account_id,
                client_id=client_id,
                payload={},
                client_updated_at=client_updated_at,
                version=1,
                last_operation_id=operation_id,
                created_at=now,
                updated_at=now,
                deleted_at=now,
            )
            return await self._repository.save(tombstone)
        if base_version != current.version:
            raise GeoSylvaSyncConflictError(current)
        return await self._repository.save(
            replace(
                current,
                client_updated_at=client_updated_at,
                version=current.version + 1,
                last_operation_id=operation_id,
                updated_at=now,
                deleted_at=now,
            )
        )

    async def list(
        self,
        account_id: UUID,
        *,
        page: int,
        size: int,
    ) -> tuple[list[GeoSylvaParcelRecord], int]:
        return await self._repository.list_for_account(
            account_id,
            offset=(page - 1) * size,
            limit=size,
        )
