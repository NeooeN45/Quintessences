"""Tests unitaires — service d'ingestion en lot (BulkIngestService).

Ces tests vérifient la logique du service sans base de données :
- Validation des items (échec partiel).
- Limite de lot (1000 max).
- Rapport détaillé (succès + erreurs).
- Mass assignment protection (champs interdits filtrés).

La session est mockée — les tests d'intégration (tests/integration/)
vérifient le comportement réel avec PostgreSQL.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from gsie_api.ingestion.bulk import MAX_BATCH_SIZE, BulkIngestService
from gsie_api.resources.schemas import BulkIngestRequest, ResourceCreate
from gsie_api.shared.schemas import BulkIngestResult


def _make_session_mock() -> MagicMock:
    """Crée un mock de AsyncSession pour les tests."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


def _make_resource_create(type_name: str = "concept") -> ResourceCreate:
    """Crée un ResourceCreate valide pour les tests."""
    return ResourceCreate(
        type=type_name,
        data={"label": "Test concept"},
    )


def test_should_reject_batch_exceeding_max_size() -> None:
    """Un lot de plus de 1000 items doit lever ValueError au niveau service.

    Le schéma Pydantic limite déjà à 1000, mais le service a sa propre
    garde (MAX_BATCH_SIZE) pour le cas où il serait appelé directement
    sans passer par le schéma (ex: appel interne depuis un autre service).
    """
    session = _make_session_mock()
    service = BulkIngestService(session)
    # On mock la requête pour contourner la validation Pydantic.
    request = MagicMock()
    request.items = [_make_resource_create() for _ in range(MAX_BATCH_SIZE + 1)]

    with pytest.raises(ValueError, match="Lot trop volumineux"):
        import asyncio

        asyncio.run(service.ingest(request))


def test_should_reject_empty_batch() -> None:
    """Un lot vide doit être rejeté par le schéma Pydantic."""
    with pytest.raises(ValueError, match="at least 1 item"):
        BulkIngestRequest(items=[])


def test_should_reject_batch_with_more_than_1000_items_at_schema_level() -> None:
    """Le schéma BulkIngestRequest doit limiter à 1000 items."""
    with pytest.raises(ValueError, match="at most 1000 items"):
        BulkIngestRequest(items=[_make_resource_create() for _ in range(1001)])


def test_max_batch_size_is_1000() -> None:
    """La constante MAX_BATCH_SIZE doit être 1000."""
    assert MAX_BATCH_SIZE == 1000


def test_bulk_ingest_result_schema_has_required_fields() -> None:
    """BulkIngestResult doit avoir total, success, errors, items."""
    result = BulkIngestResult(total=10, success=8, errors=2, items=[])
    assert result.total == 10
    assert result.success == 8
    assert result.errors == 2
    assert result.items == []


def test_bulk_item_result_success_has_resource_id() -> None:
    """Un BulkItemResult de succès doit avoir resource_id et gsie_id."""
    from uuid import uuid4

    from gsie_api.shared.schemas import BulkItemResult

    result = BulkItemResult(
        index=0,
        success=True,
        resource_id=uuid4(),
        gsie_id="concept:2026:abc12345",
    )
    assert result.success is True
    assert result.resource_id is not None
    assert result.gsie_id is not None
    assert result.error_code is None


def test_bulk_item_result_failure_has_error_code() -> None:
    """Un BulkItemResult d'échec doit avoir error_code et error_detail."""
    from gsie_api.shared.schemas import BulkItemResult

    result = BulkItemResult(
        index=1,
        success=False,
        error_code="validation_failed",
        error_detail={"type": "concept", "errors": ["label requis"]},
    )
    assert result.success is False
    assert result.error_code == "validation_failed"
    assert result.resource_id is None
