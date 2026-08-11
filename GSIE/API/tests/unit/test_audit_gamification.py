"""Tests unitaires — endpoints Audit et Gamification du dashboard.

Couvre les lignes résiduelles (return des endpoints) dans :
- gsie_api/audit/router.py (ligne 98)
- gsie_api/gamification/router.py (ligne 102)

Les données sont statiques (Phase 4 — implémentation progressive).
On vérifie le contrat : structure JSON, types, champs attendus.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.audit.router import get_audit_service
from gsie_api.audit.service import AuditEntry
from gsie_api.core.auth import create_access_token


def _auth_headers() -> dict[str, str]:
    """Génère un token JWT valide avec rôle reader pour les endpoints protégés."""
    token = create_access_token(subject=str(uuid4()), claims={"roles": ["reader"]})
    return {"Authorization": f"Bearer {token}"}


def _audit_app() -> object:
    app = create_app()
    service = AsyncMock()
    service.list = AsyncMock(
        return_value=(
            [
                AuditEntry(
                    id=uuid4(),
                    timestamp=datetime.now(UTC),
                    actor_id=None,
                    actor_email=None,
                    action="login",
                    resource_type="auth",
                    resource_id=None,
                    ip_address=None,
                    user_agent=None,
                    organisation_id=None,
                    workspace_id=None,
                    status_code=200,
                    method="POST",
                    path="/auth/login/password",
                    details={},
                    trace_id=None,
                )
            ],
            1,
        )
    )
    app.dependency_overrides[get_audit_service] = lambda: service
    return app


class TestAuditLogsEndpoint:
    """GET /api/v1/audit-logs — liste des entrées d'audit."""

    def should_return_audit_logs_list(self) -> None:
        """L'endpoint retourne une liste non vide d'entrées d'audit."""
        app = _audit_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/audit-logs",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

    def should_return_well_formed_audit_entries(self) -> None:
        """Chaque entrée contient les champs attendus (id, timestamp, user, action)."""
        app = _audit_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/audit-logs",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        for entry in response.json()["items"]:
            assert "id" in entry
            assert "timestamp" in entry
            assert "actor_id" in entry
            assert "action" in entry
            assert "resource_type" in entry
            assert "ip_address" in entry
            assert "details" in entry


class TestGamificationStatsEndpoint:
    """GET /api/v1/gamification/stats — statistiques d'engagement."""

    def should_return_gamification_stats(self) -> None:
        """L'endpoint retourne les stats avec badges, goals et streak."""
        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/gamification/stats",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "badges" in data
        assert "goals" in data
        assert "streak" in data

    def should_return_non_empty_badges_list(self) -> None:
        """La liste des badges n'est pas vide (données statiques Phase 4)."""
        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/gamification/stats",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        badges = response.json()["badges"]
        assert isinstance(badges, list)
        assert len(badges) > 0
        for badge in badges:
            assert "id" in badge
            assert "name" in badge
            assert "unlocked" in badge

    def should_return_goals_with_progress(self) -> None:
        """Chaque objectif contient current, target et unit."""
        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/gamification/stats",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        goals = response.json()["goals"]
        assert isinstance(goals, list)
        assert len(goals) > 0
        for goal in goals:
            assert "current" in goal
            assert "target" in goal
            assert "unit" in goal
