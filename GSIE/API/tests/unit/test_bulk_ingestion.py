"""Tests unitaires — ingestion bulk (POST /resources/bulk).

Couvre les schémas et constantes de `ingestion/bulk.py` :
- MAX_BATCH_SIZE (limite dure 1000)
- BulkIngestResult / BulkItemResult (shared/schemas.py)
- BulkIngestRequest (resources/schemas.py)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from gsie_api.ingestion.bulk import MAX_BATCH_SIZE
from gsie_api.resources.schemas import BulkIngestRequest, ResourceCreate
from gsie_api.shared.schemas import BulkIngestResult, BulkItemResult


class TestMaxBatchSize:
    """Constante de limite dure."""

    def should_be_1000(self) -> None:
        assert MAX_BATCH_SIZE == 1000


class TestBulkItemResult:
    """Schéma de résultat par item."""

    def should_track_success_with_resource_id(self) -> None:
        result = BulkItemResult(
            index=0,
            success=True,
            resource_id=uuid4(),
            gsie_id="assertion_001",
        )
        assert result.success is True
        assert result.error_code is None

    def should_track_failure_with_error_code(self) -> None:
        result = BulkItemResult(
            index=1,
            success=False,
            error_code="VALIDATION_ERROR",
            error_detail="Type inconnu",
        )
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"
        assert result.resource_id is None

    def should_reject_extra_fields(self) -> None:
        with pytest.raises(ValueError):
            BulkItemResult(index=0, success=True, extra_field="not allowed")  # type: ignore[call-arg]


class TestBulkIngestResult:
    """Schéma de rapport global."""

    def should_track_summary_counts(self) -> None:
        result = BulkIngestResult(
            total=10,
            success=8,
            errors=2,
            items=[
                BulkItemResult(index=0, success=True, resource_id=uuid4()),
                BulkItemResult(index=1, success=False, error_code="ERR"),
            ],
        )
        assert result.total == 10
        assert result.success == 8
        assert result.errors == 2
        assert len(result.items) == 2

    def should_reject_negative_counts(self) -> None:
        with pytest.raises(ValueError):
            BulkIngestResult(total=-1, success=0, errors=0, items=[])

    def should_reject_extra_fields(self) -> None:
        with pytest.raises(ValueError):
            BulkIngestResult(  # type: ignore[call-arg]
                total=1, success=1, errors=0, items=[], extra="not allowed"
            )


class TestBulkIngestRequest:
    """Schéma de requête bulk."""

    def should_accept_valid_items(self) -> None:
        req = BulkIngestRequest(
            items=[
                ResourceCreate(
                    type="assertion",
                    data={"claim": "Le chêne pousse en France"},
                ),
            ]
        )
        assert len(req.items) == 1

    def should_reject_empty_items(self) -> None:
        with pytest.raises(ValueError):
            BulkIngestRequest(items=[])

    def should_reject_extra_fields(self) -> None:
        with pytest.raises(ValueError):
            BulkIngestRequest(  # type: ignore[call-arg]
                items=[ResourceCreate(type="assertion", data={})],
                extra_field="not allowed",
            )
