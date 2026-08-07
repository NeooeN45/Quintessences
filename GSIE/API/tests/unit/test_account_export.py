"""Couverture de l'export RGPD du compte courant (AccountExportService)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.auth.account_export import AccountExportService

_NOW = datetime.now(UTC)


def _scalars_result(rows: tuple[object, ...]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = list(rows)
    return result


def _join_result(rows: tuple[object, ...]) -> MagicMock:
    result = MagicMock()
    result.all.return_value = list(rows)
    return result


def _session() -> MagicMock:
    session = MagicMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    return session


async def should_raise_when_account_is_missing() -> None:
    session = _session()
    session.get.return_value = None
    service = AccountExportService(session)
    with pytest.raises(ValueError, match="Compte introuvable"):
        await service.export(uuid4())


async def should_export_full_account_payload_with_populated_fields() -> None:
    account_id = uuid4()
    session = _session()
    session.get.return_value = SimpleNamespace(
        id=account_id,
        display_name="Forestier Test",
        status="active",
        created_at=_NOW,
        updated_at=_NOW,
    )

    identity_link = SimpleNamespace(
        provider="google",
        issuer="https://accounts.google.com",
        subject="sub-1",
        email_normalized="forestier@example.com",
        email_verified=True,
        last_authenticated_at=_NOW,
    )
    role = SimpleNamespace(application="geosylva", role="admin")
    organisation = SimpleNamespace(slug="gsie", display_name="GSIE")
    member = SimpleNamespace(organisation_id=uuid4(), role="owner", joined_at=_NOW)
    plan = SimpleNamespace(code="pro")
    subscription = SimpleNamespace(
        id=uuid4(),
        owner_type="account",
        provider="stripe",
        status="active",
        current_period_start=_NOW,
        current_period_end=_NOW,
        cancel_at_period_end=False,
    )
    entitlement = SimpleNamespace(
        feature_code="export",
        status="active",
        valid_from=_NOW,
        valid_until=_NOW,
    )
    active_session = SimpleNamespace(
        issued_at=_NOW,
        last_seen_at=_NOW,
        device_name="Pixel 8",
        user_agent="GeoSylva/1.0",
        ip_address="127.0.0.1",
        revoked_at=_NOW,
    )
    audit_event = SimpleNamespace(
        timestamp=_NOW,
        action="login",
        resource_type="account",
        resource_id=str(account_id),
        status_code=200,
        details={"ip": "127.0.0.1"},
    )

    session.execute = AsyncMock(
        side_effect=[
            _scalars_result((identity_link,)),
            _scalars_result((role,)),
            _join_result(((member, organisation),)),
            _join_result(((subscription, plan),)),
            _scalars_result((entitlement,)),
            _scalars_result((active_session,)),
            _scalars_result((audit_event,)),
        ]
    )

    service = AccountExportService(session)
    result = await service.export(account_id)

    assert result["account"]["id"] == str(account_id)
    assert result["account"]["display_name"] == "Forestier Test"
    assert result["identity_links"] == [
        {
            "provider": "google",
            "issuer": "https://accounts.google.com",
            "subject": "sub-1",
            "email": "forestier@example.com",
            "email_verified": True,
            "last_authenticated_at": _NOW.isoformat(),
        }
    ]
    assert result["roles"] == [{"application": "geosylva", "role": "admin"}]
    assert result["organisations"][0]["organisation_slug"] == "gsie"
    assert result["subscriptions"][0]["plan_code"] == "pro"
    assert result["subscriptions"][0]["current_period_start"] == _NOW.isoformat()
    assert result["entitlements"][0]["valid_until"] == _NOW.isoformat()
    assert result["sessions"][0]["revoked_at"] == _NOW.isoformat()
    assert result["audit_events"][0]["details"] == {"ip": "127.0.0.1"}


async def should_export_empty_collections_with_null_optional_fields() -> None:
    account_id = uuid4()
    session = _session()
    session.get.return_value = SimpleNamespace(
        id=account_id,
        display_name=None,
        status="active",
        created_at=_NOW,
        updated_at=_NOW,
    )

    identity_link = SimpleNamespace(
        provider="oidc",
        issuer="https://auth.example.com",
        subject="sub-2",
        email_normalized="autre@example.com",
        email_verified=False,
        last_authenticated_at=None,
    )
    plan = SimpleNamespace(code="free")
    subscription = SimpleNamespace(
        id=uuid4(),
        owner_type="account",
        provider="none",
        status="trialing",
        current_period_start=None,
        current_period_end=None,
        cancel_at_period_end=True,
    )
    entitlement = SimpleNamespace(
        feature_code="export",
        status="active",
        valid_from=_NOW,
        valid_until=None,
    )
    active_session = SimpleNamespace(
        issued_at=_NOW,
        last_seen_at=_NOW,
        device_name=None,
        user_agent=None,
        ip_address=None,
        revoked_at=None,
    )

    session.execute = AsyncMock(
        side_effect=[
            _scalars_result((identity_link,)),
            _scalars_result(()),
            _join_result(()),
            _join_result(((subscription, plan),)),
            _scalars_result((entitlement,)),
            _scalars_result((active_session,)),
            _scalars_result(()),
        ]
    )

    service = AccountExportService(session)
    result = await service.export(account_id)

    assert result["identity_links"][0]["last_authenticated_at"] is None
    assert result["roles"] == []
    assert result["organisations"] == []
    assert result["subscriptions"][0]["current_period_start"] is None
    assert result["subscriptions"][0]["current_period_end"] is None
    assert result["entitlements"][0]["valid_until"] is None
    assert result["sessions"][0]["revoked_at"] is None
    assert result["audit_events"] == []
