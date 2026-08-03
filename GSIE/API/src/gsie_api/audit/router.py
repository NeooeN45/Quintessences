"""Router Audit — journaux d'audit du dashboard.

Endpoint :
- GET /audit-logs — liste des entrées d'audit

Sécurité : auth JWT obligatoire (lecture seule).

Note : les données sont actuellement statiques. Un vrai système d'audit
sera implémenté pendant la Phase 4 (middleware traçant les mutations
ressources, diagnostics, recommandations).
"""

from typing import Any

from fastapi import APIRouter, Request, Response

from gsie_api.audit.schemas import AuditLog
from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineReadUser

router = APIRouter(prefix="/audit-logs", tags=["audit"])

# Données statiques — remplacées par une source réelle quand le
# middleware d'audit sera implémenté (mutations ressources, moteurs).
_LOGS: list[dict[str, Any]] = [
    {
        "id": "aud-001",
        "timestamp": "2026-08-02T18:42:11Z",
        "user": "admin",
        "action": "create",
        "resource": "resource:forest-stand-075",
        "ip": "127.0.0.1",
        "details": {"type": "forest_stand", "source": "dashboard"},
    },
    {
        "id": "aud-002",
        "timestamp": "2026-08-02T18:35:02Z",
        "user": "admin",
        "action": "update",
        "resource": "knowledge:knb-0042",
        "ip": "127.0.0.1",
        "details": {"field": "confidence", "old": 0.78, "new": 0.85},
    },
    {
        "id": "aud-003",
        "timestamp": "2026-08-02T17:58:44Z",
        "user": "admin",
        "action": "export",
        "resource": "resources:bulk",
        "ip": "127.0.0.1",
        "details": {"format": "csv", "count": 42},
    },
    {
        "id": "aud-004",
        "timestamp": "2026-08-02T17:12:30Z",
        "user": "admin",
        "action": "delete",
        "resource": "resource:dataset-old-13",
        "ip": "127.0.0.1",
        "details": {"reason": "obsolescence", "soft_delete": True},
    },
    {
        "id": "aud-005",
        "timestamp": "2026-08-02T16:40:18Z",
        "user": "admin",
        "action": "create",
        "resource": "knowledge:knb-0043",
        "ip": "127.0.0.1",
        "details": {"domain": "pedology", "source": "ingestion"},
    },
    {
        "id": "aud-006",
        "timestamp": "2026-08-02T15:22:07Z",
        "user": "admin",
        "action": "update",
        "resource": "resource:climate-station-31",
        "ip": "127.0.0.1",
        "details": {"field": "status", "old": "draft", "new": "validated"},
    },
]


@router.get(
    "",
    response_model=list[AuditLog],
    summary="Liste des entrées du journal d'audit",
    description=(
        "Retourne les entrées d'audit (actions create/update/delete/export). "
        "Données actuellement statiques — seront alimentées par le "
        "middleware d'audit quand il sera implémenté (Phase 4)."
    ),
)
@_limiter.limit("30/minute")
async def list_audit_logs(
    request: Request,
    response: Response,
    _user: EngineReadUser,
) -> list[AuditLog]:
    """Liste des entrées du journal d'audit."""
    return [AuditLog(**log) for log in _LOGS]
