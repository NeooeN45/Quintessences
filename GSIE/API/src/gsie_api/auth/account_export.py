"""Export RGPD des données personnelles du compte courant.

L'export est volontairement allowlisté : les secrets d'authentification,
hashes, tokens, clés et détails de paiement ne sont jamais sérialisés.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.infrastructure.models.accounts import (
    AccountRoleModel,
    ActiveSessionModel,
    IdentityProviderLinkModel,
    UserAccountModel,
)
from gsie_api.infrastructure.models.audit_log import AuditLogModel
from gsie_api.infrastructure.models.billing import (
    EntitlementModel,
    PlanModel,
    SubscriptionModel,
)
from gsie_api.infrastructure.models.organisations import (
    OrganisationMemberModel,
    OrganisationModel,
)


class AccountExportService:
    """Construit un export RGPD sans exposer les secrets techniques."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def export(self, account_id: UUID) -> dict[str, Any]:
        account = await self._session.get(UserAccountModel, account_id)
        if account is None:
            raise ValueError("Compte introuvable")
        identity_links = await self._identity_links(account_id)
        roles = await self._roles(account_id)
        memberships = await self._memberships(account_id)
        subscriptions = await self._subscriptions(account_id)
        entitlements = await self._entitlements(account_id)
        sessions = await self._sessions(account_id)
        audit_events = await self._audit_events(account_id)
        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "account": {
                "id": str(account.id),
                "display_name": account.display_name,
                "status": account.status,
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat(),
            },
            "identity_links": identity_links,
            "roles": roles,
            "organisations": memberships,
            "subscriptions": subscriptions,
            "entitlements": entitlements,
            "sessions": sessions,
            "audit_events": audit_events,
        }

    async def _identity_links(self, account_id: UUID) -> list[dict[str, object]]:
        rows = (
            (
                await self._session.execute(
                    select(IdentityProviderLinkModel).where(
                        IdentityProviderLinkModel.account_id == account_id,
                        IdentityProviderLinkModel.revoked_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "provider": row.provider,
                "issuer": row.issuer,
                "subject": row.subject,
                "email": row.email_normalized,
                "email_verified": row.email_verified,
                "last_authenticated_at": (
                    row.last_authenticated_at.isoformat() if row.last_authenticated_at else None
                ),
            }
            for row in rows
        ]

    async def _roles(self, account_id: UUID) -> list[dict[str, str]]:
        rows = (
            (
                await self._session.execute(
                    select(AccountRoleModel).where(AccountRoleModel.account_id == account_id)
                )
            )
            .scalars()
            .all()
        )
        return [{"application": row.application, "role": row.role} for row in rows]

    async def _memberships(self, account_id: UUID) -> list[dict[str, object]]:
        statement = (
            select(OrganisationMemberModel, OrganisationModel)
            .join(
                OrganisationModel,
                OrganisationModel.id == OrganisationMemberModel.organisation_id,
            )
            .where(
                OrganisationMemberModel.account_id == account_id,
                OrganisationMemberModel.revoked_at.is_(None),
            )
        )
        rows = (await self._session.execute(statement)).all()
        return [
            {
                "organisation_id": str(member.organisation_id),
                "organisation_slug": organisation.slug,
                "organisation_name": organisation.display_name,
                "role": member.role,
                "joined_at": member.joined_at.isoformat(),
            }
            for member, organisation in rows
        ]

    async def _subscriptions(self, account_id: UUID) -> list[dict[str, object]]:
        statement = (
            select(SubscriptionModel, PlanModel)
            .join(PlanModel, PlanModel.id == SubscriptionModel.plan_id)
            .where(SubscriptionModel.account_id == account_id)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            {
                "id": str(subscription.id),
                "owner_type": subscription.owner_type,
                "plan_code": plan.code,
                "provider": subscription.provider,
                "status": subscription.status,
                "current_period_start": (
                    subscription.current_period_start.isoformat()
                    if subscription.current_period_start
                    else None
                ),
                "current_period_end": (
                    subscription.current_period_end.isoformat()
                    if subscription.current_period_end
                    else None
                ),
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
            for subscription, plan in rows
        ]

    async def _entitlements(self, account_id: UUID) -> list[dict[str, object]]:
        rows = (
            (
                await self._session.execute(
                    select(EntitlementModel).where(EntitlementModel.account_id == account_id)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "feature_code": row.feature_code,
                "status": row.status,
                "valid_from": row.valid_from.isoformat(),
                "valid_until": row.valid_until.isoformat() if row.valid_until else None,
            }
            for row in rows
        ]

    async def _sessions(self, account_id: UUID) -> list[dict[str, object]]:
        rows = (
            (
                await self._session.execute(
                    select(ActiveSessionModel).where(ActiveSessionModel.account_id == account_id)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "issued_at": row.issued_at.isoformat(),
                "last_seen_at": row.last_seen_at.isoformat(),
                "device_name": row.device_name,
                "user_agent": row.user_agent,
                "ip_address": row.ip_address,
                "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
            }
            for row in rows
        ]

    async def _audit_events(self, account_id: UUID) -> list[dict[str, object]]:
        rows = (
            (
                await self._session.execute(
                    select(AuditLogModel)
                    .where(AuditLogModel.actor_id == account_id)
                    .order_by(AuditLogModel.timestamp.asc())
                    .limit(10_000)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "status_code": row.status_code,
                "details": dict(row.details),
            }
            for row in rows
        ]
