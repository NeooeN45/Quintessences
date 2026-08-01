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
from sqlalchemy.exc import IntegrityError

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


# --- Divulgation : le texte du pilote ne doit jamais sortir ---


class _ViolationCleEtrangereErrorError(Exception):
    """Imite `asyncpg.exceptions.ForeignKeyViolationError`.

    `_champ_de_reference_fautif` reconnaît la violation par le *nom* de la
    classe, pas par son type — asyncpg n'est pas importable sans connexion.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


_ViolationCleEtrangereErrorError.__name__ = "ForeignKeyViolationError"


def _integrity_error(orig: Exception) -> IntegrityError:
    """Emballe une exception pilote comme SQLAlchemy le fait."""
    return IntegrityError("INSERT INTO ...", {}, orig)


def test_detail_integrite_ne_divulgue_pas_le_texte_du_pilote() -> None:
    """Le rapport rendu au client ne doit porter ni schéma, ni table, ni contrainte.

    `str(exc.orig)` d'asyncpg décrit la ligne fautive au complet. Le rendre
    transformait `POST /resources/bulk` en cartographie des schémas
    cloisonnés par la RFC-0029, pour tout porteur du rôle `writer`.
    """
    brut = (
        'duplicate key value violates unique constraint "resource_gsie_id_key"\n'
        "DETAIL:  Key (gsie_id)=(entity:2026:deadbeef) already exists.\n"
        "SCHEMA NAME:  gsie_rgpd\nTABLE NAME:  data_subject"
    )
    service = BulkIngestService(_make_session_mock())

    detail = service._detail_integrite(0, _integrity_error(Exception(brut)), {"label": "x"})

    assert isinstance(detail, str)
    for fuite in ("resource_gsie_id_key", "gsie_rgpd", "data_subject", "DETAIL", "SCHEMA"):
        assert fuite not in detail, f"le motif rendu divulgue « {fuite} »"


def test_detail_integrite_nomme_une_reference_venue_de_la_charge_utile() -> None:
    """Une clé étrangère pendante fournie par l'appelant est nommée.

    L'appelant a lui-même écrit la valeur : la lui nommer ne lui apprend
    rien qu'il ignore, et lui permet de corriger son lot. C'est le même
    contrat que le chemin unitaire (`_references_nommees`).
    """
    violation = _ViolationCleEtrangereErrorError(
        'Key (source_id)=(00000000-0000-0000-0000-000000000000) is not present in table "resource".'
    )
    service = BulkIngestService(_make_session_mock())

    detail = service._detail_integrite(
        3, _integrity_error(violation), {"source_id": "00000000-0000-0000-0000-000000000000"}
    )

    assert "Référence inexistante pour source_id" in detail


def test_detail_integrite_reste_opaque_si_la_colonne_ne_vient_pas_du_client() -> None:
    """Une violation sur une colonne gérée par le service reste opaque.

    Le client n'a pas écrit `author_id` : le lui nommer lui apprendrait
    l'existence d'une colonne qu'il n'a pas soumise.
    """
    violation = _ViolationCleEtrangereErrorError(
        'Key (author_id)=(00000000-0000-0000-0000-000000000000) is not present in table "resource".'
    )
    service = BulkIngestService(_make_session_mock())

    detail = service._detail_integrite(1, _integrity_error(violation), {"label": "x"})

    assert "author_id" not in detail
    assert "Conflit d'intégrité" in detail
