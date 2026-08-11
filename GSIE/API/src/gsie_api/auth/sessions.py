"""Sessions actives — traçage et révocation par appareil.

Chaque émission de tokens crée une entrée active_session. L'utilisateur
peut lister ses sessions actives et en révoquer une sélectivement, ce
qui marque le jti comme révoqué et invalide le refresh token associé.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import select, update

from gsie_api.infrastructure.models.accounts import ActiveSessionModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """Vue d'une session active pour l'utilisateur."""

    id: UUID
    jti: str
    device_name: str | None
    user_agent: str | None
    ip_address: str | None
    issued_at: datetime
    last_seen_at: datetime
    is_current: bool = False


class SessionRepositoryProtocol(Protocol):
    """Contrat de persistance des sessions actives."""

    async def create_session(
        self,
        account_id: UUID,
        jti: str,
        refresh_jti: str | None,
        device_name: str | None,
        user_agent: str | None,
        ip_address: str | None,
    ) -> SessionInfo: ...

    async def list_active_sessions(self, account_id: UUID) -> list[SessionInfo]: ...

    async def rotate_session(
        self, current_jti: str, new_jti: str, new_refresh_jti: str
    ) -> bool: ...

    async def get_refresh_jti(self, account_id: UUID, session_id: UUID) -> str | None: ...

    async def list_refresh_jtis(
        self, account_id: UUID, except_jti: str | None = None
    ) -> list[str]: ...

    async def revoke_session(self, account_id: UUID, session_id: UUID) -> bool: ...

    async def revoke_all_sessions(self, account_id: UUID, except_jti: str | None = None) -> int: ...

    async def revoke_by_jti(self, jti: str) -> bool: ...

    async def touch_session(self, jti: str) -> None: ...


class SqlAlchemySessionRepository:
    """Dépôt transactionnel des sessions actives."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        account_id: UUID,
        jti: str,
        refresh_jti: str | None,
        device_name: str | None,
        user_agent: str | None,
        ip_address: str | None,
    ) -> SessionInfo:
        model = ActiveSessionModel(
            account_id=account_id,
            jti=jti,
            refresh_jti=refresh_jti,
            device_name=device_name,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_info(model)

    async def list_active_sessions(self, account_id: UUID) -> list[SessionInfo]:
        stmt = (
            select(ActiveSessionModel)
            .where(
                ActiveSessionModel.account_id == account_id,
                ActiveSessionModel.revoked_at.is_(None),
            )
            .order_by(ActiveSessionModel.last_seen_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_info(m) for m in rows]

    async def rotate_session(self, current_jti: str, new_jti: str, new_refresh_jti: str) -> bool:
        stmt = (
            update(ActiveSessionModel)
            .where(
                ActiveSessionModel.jti == current_jti,
                ActiveSessionModel.revoked_at.is_(None),
            )
            .values(jti=new_jti, refresh_jti=new_refresh_jti, last_seen_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_refresh_jti(self, account_id: UUID, session_id: UUID) -> str | None:
        stmt = select(ActiveSessionModel.refresh_jti).where(
            ActiveSessionModel.account_id == account_id,
            ActiveSessionModel.id == session_id,
            ActiveSessionModel.revoked_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_refresh_jtis(self, account_id: UUID, except_jti: str | None = None) -> list[str]:
        conditions = [
            ActiveSessionModel.account_id == account_id,
            ActiveSessionModel.revoked_at.is_(None),
            ActiveSessionModel.refresh_jti.is_not(None),
        ]
        if except_jti is not None:
            conditions.append(ActiveSessionModel.jti != except_jti)
        stmt = select(ActiveSessionModel.refresh_jti).where(*conditions)
        return [jti for jti in (await self._session.execute(stmt)).scalars().all() if jti]

    async def revoke_session(self, account_id: UUID, session_id: UUID) -> bool:
        stmt = (
            update(ActiveSessionModel)
            .where(
                ActiveSessionModel.account_id == account_id,
                ActiveSessionModel.id == session_id,
                ActiveSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def revoke_all_sessions(self, account_id: UUID, except_jti: str | None = None) -> int:
        conditions = [
            ActiveSessionModel.account_id == account_id,
            ActiveSessionModel.revoked_at.is_(None),
        ]
        if except_jti is not None:
            conditions.append(ActiveSessionModel.jti != except_jti)
        stmt = update(ActiveSessionModel).where(*conditions).values(revoked_at=datetime.now(UTC))
        result = await self._session.execute(stmt)
        return result.rowcount

    async def revoke_by_jti(self, jti: str) -> bool:
        stmt = (
            update(ActiveSessionModel)
            .where(
                ActiveSessionModel.jti == jti,
                ActiveSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def touch_session(self, jti: str) -> None:
        stmt = (
            update(ActiveSessionModel)
            .where(
                ActiveSessionModel.jti == jti,
                ActiveSessionModel.revoked_at.is_(None),
            )
            .values(last_seen_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    @staticmethod
    def _to_info(model: ActiveSessionModel) -> SessionInfo:
        return SessionInfo(
            id=model.id,
            jti=model.jti,
            device_name=model.device_name,
            user_agent=model.user_agent,
            ip_address=model.ip_address,
            issued_at=model.issued_at,
            last_seen_at=model.last_seen_at,
        )


class SessionService:
    """Orchestre les sessions actives et leur révocation."""

    def __init__(self, repository: SessionRepositoryProtocol) -> None:
        self._repository = repository

    async def register_session(
        self,
        account_id: UUID,
        jti: str,
        refresh_jti: str | None,
        device_name: str | None,
        user_agent: str | None,
        ip_address: str | None,
    ) -> SessionInfo:
        return await self._repository.create_session(
            account_id, jti, refresh_jti, device_name, user_agent, ip_address
        )

    async def list_sessions(self, account_id: UUID) -> list[SessionInfo]:
        return await self._repository.list_active_sessions(account_id)

    async def rotate_session(self, current_jti: str, new_jti: str, new_refresh_jti: str) -> bool:
        return await self._repository.rotate_session(current_jti, new_jti, new_refresh_jti)

    async def get_refresh_jti(self, account_id: UUID, session_id: UUID) -> str | None:
        return await self._repository.get_refresh_jti(account_id, session_id)

    async def list_refresh_jtis(self, account_id: UUID, except_jti: str | None = None) -> list[str]:
        return await self._repository.list_refresh_jtis(account_id, except_jti)

    async def revoke_session(self, account_id: UUID, session_id: UUID) -> bool:
        return await self._repository.revoke_session(account_id, session_id)

    async def revoke_all_sessions(self, account_id: UUID, except_jti: str | None = None) -> int:
        return await self._repository.revoke_all_sessions(account_id, except_jti)

    async def revoke_by_jti(self, jti: str) -> bool:
        return await self._repository.revoke_by_jti(jti)
