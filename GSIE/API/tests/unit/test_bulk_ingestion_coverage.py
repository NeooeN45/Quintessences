"""Tests unitaires — couverture complète de ingestion/bulk.py.

Couvre les chemins non testés du BulkIngestService (lignes 102-187,
224-242, 252-257) :
- ingest : succès, erreurs de validation, type inconnu, integrité, commit critique
- _create_one : création réussie, erreur de validation
- _insert_resource : insertion sans commit
- _detail_integrite : référence nommée vs générique
"""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from gsie_api.ingestion.bulk import MAX_BATCH_SIZE, BulkIngestService
from gsie_api.resources.schemas import BulkIngestRequest, ResourceCreate


def _make_session() -> AsyncMock:
    """Crée une session DB mockée avec begin_nested supportant async with."""
    session = AsyncMock()
    nested = AsyncMock()
    nested.__aenter__.return_value = None
    nested.__aexit__.return_value = False
    session.begin_nested = MagicMock(return_value=nested)
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _configure_unitaire(mock_rs_cls: MagicMock) -> MagicMock:
    """Configure un ResourceService mocké avec des valeurs par défaut valides."""
    mock_unitaire = cast(MagicMock, mock_rs_cls.return_value)
    mock_unitaire._get_model_cls.return_value = MagicMock(name="Model")
    mock_unitaire._filtrer_et_coercer.return_value = {"claim": "test"}
    mock_unitaire._refuser_grain_absent = AsyncMock(return_value=None)
    mock_unitaire._generate_gsie_id.return_value = "assertion:2026:abc12345"
    mock_read = MagicMock()
    mock_read.id = uuid4()
    mock_read.gsie_id = "assertion_001"
    mock_unitaire._to_resource_read.return_value = mock_read
    mock_unitaire._create_revision = AsyncMock(return_value=None)
    return mock_unitaire


class TestBulkIngestServiceCoverage:
    """Couverture complète des chemins non testés de BulkIngestService."""

    async def should_return_success_result_when_all_items_valid(self) -> None:
        # Arrange
        session = _make_session()
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
        ):
            _configure_unitaire(mock_rs_cls)
            mock_validate.return_value = []
            service = BulkIngestService(session)
            request = BulkIngestRequest(
                items=[
                    ResourceCreate(
                        type="assertion",
                        data={"claim": "Le chêne pousse en France"},
                    ),
                ]
            )

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.total == 1
        assert result.success == 1
        assert result.errors == 0
        assert result.items[0].success is True
        assert result.items[0].resource_id is not None
        assert result.items[0].gsie_id == "assertion_001"
        session.commit.assert_awaited_once()

    async def should_mark_validation_failed_when_create_one_raises_validation_error(
        self,
    ) -> None:
        # Arrange
        session = _make_session()
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
        ):
            mock_unitaire = _configure_unitaire(mock_rs_cls)
            mock_unitaire._get_model_cls.return_value = MagicMock()
            mock_validate.return_value = ["Le champ claim est requis"]
            service = BulkIngestService(session)
            request = BulkIngestRequest(items=[ResourceCreate(type="assertion", data={})])

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.success == 0
        assert result.errors == 1
        assert result.items[0].success is False
        assert result.items[0].error_code == "validation_failed"
        error_detail = result.items[0].error_detail
        assert isinstance(error_detail, dict)
        assert error_detail["type"] == "assertion"
        assert error_detail["errors"] == ["Le champ claim est requis"]

    async def should_mark_unknown_type_when_create_one_raises_value_error(self) -> None:
        # Arrange
        session = _make_session()
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
        ):
            mock_unitaire = cast(MagicMock, mock_rs_cls.return_value)
            mock_unitaire._get_model_cls.side_effect = ValueError("Type inconnu : foobar")
            mock_validate.return_value = []
            service = BulkIngestService(session)
            request = BulkIngestRequest(items=[ResourceCreate(type="foobar", data={})])

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.errors == 1
        assert result.items[0].success is False
        assert result.items[0].error_code == "unknown_type"
        error_detail = result.items[0].error_detail
        assert isinstance(error_detail, str)
        assert "Type inconnu" in error_detail

    async def should_name_reference_field_when_integrity_error_matches_payload(
        self,
    ) -> None:
        # Arrange
        session = _make_session()
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
            patch("gsie_api.ingestion.bulk._champ_de_reference_fautif") as mock_champ,
        ):
            mock_unitaire = _configure_unitaire(mock_rs_cls)
            mock_validate.return_value = []
            mock_unitaire._filtrer_et_coercer.return_value = {"source_id": str(uuid4())}
            service = BulkIngestService(session)
            integrity_exc = IntegrityError("INSERT", {}, Exception("fk violation"))
            service._insert_resource = AsyncMock(side_effect=integrity_exc)  # type: ignore[method-assign]
            mock_champ.return_value = "source_id"
            request = BulkIngestRequest(
                items=[
                    ResourceCreate(
                        type="assertion",
                        gsie_id="assertion_001",
                        data={"source_id": str(uuid4())},
                    ),
                ]
            )

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.errors == 1
        assert result.items[0].success is False
        assert result.items[0].error_code == "integrity_error"
        error_detail = result.items[0].error_detail
        assert isinstance(error_detail, str)
        assert "source_id" in error_detail
        assert "Référence inexistante" in error_detail

    async def should_return_generic_message_when_integrity_field_not_in_payload(
        self,
    ) -> None:
        # Arrange
        session = _make_session()
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
            patch("gsie_api.ingestion.bulk._champ_de_reference_fautif") as mock_champ,
        ):
            _configure_unitaire(mock_rs_cls)
            mock_validate.return_value = []
            service = BulkIngestService(session)
            integrity_exc = IntegrityError("INSERT", {}, Exception("unique violation"))
            service._insert_resource = AsyncMock(side_effect=integrity_exc)  # type: ignore[method-assign]
            mock_champ.return_value = "internal_field"
            request = BulkIngestRequest(
                items=[ResourceCreate(type="assertion", data={"claim": "test"})]
            )

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.items[0].error_code == "integrity_error"
        error_detail = result.items[0].error_detail
        assert isinstance(error_detail, str)
        assert "Conflit d'intégrité" in error_detail

    async def should_return_generic_message_when_no_reference_field_found(self) -> None:
        # Arrange
        session = _make_session()
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
            patch("gsie_api.ingestion.bulk._champ_de_reference_fautif") as mock_champ,
        ):
            _configure_unitaire(mock_rs_cls)
            mock_validate.return_value = []
            service = BulkIngestService(session)
            integrity_exc = IntegrityError("INSERT", {}, Exception("unique violation"))
            service._insert_resource = AsyncMock(side_effect=integrity_exc)  # type: ignore[method-assign]
            mock_champ.return_value = None
            request = BulkIngestRequest(
                items=[ResourceCreate(type="assertion", data={"claim": "test"})]
            )

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.items[0].error_code == "integrity_error"
        error_detail = result.items[0].error_detail
        assert isinstance(error_detail, str)
        assert "Conflit d'intégrité" in error_detail

    async def should_reject_all_items_when_commit_raises_integrity_error(self) -> None:
        # Arrange
        session = _make_session()
        session.commit = AsyncMock(side_effect=IntegrityError("COMMIT", {}, Exception("critical")))
        with (
            patch("gsie_api.ingestion.bulk.ResourceService") as mock_rs_cls,
            patch("gsie_api.ingestion.bulk.validate_resource_data") as mock_validate,
        ):
            _configure_unitaire(mock_rs_cls)
            mock_validate.return_value = []
            service = BulkIngestService(session)
            request = BulkIngestRequest(
                items=[
                    ResourceCreate(type="assertion", data={"claim": "test1"}),
                    ResourceCreate(type="assertion", data={"claim": "test2"}),
                ]
            )

            # Act
            result = await service.ingest(request)

        # Assert
        assert result.total == 2
        assert result.success == 0
        assert result.errors == 2
        assert all(item.error_code == "transaction_failed" for item in result.items)
        session.rollback.assert_awaited_once()

    async def should_raise_value_error_when_batch_exceeds_max_size(self) -> None:
        # Arrange
        session = _make_session()
        with patch("gsie_api.ingestion.bulk.ResourceService"):
            service = BulkIngestService(session)
            request = MagicMock()
            request.items = [MagicMock()] * (MAX_BATCH_SIZE + 1)

            # Act & Assert
            with pytest.raises(ValueError, match="Lot trop volumineux"):
                await service.ingest(request)
