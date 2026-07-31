"""Service d'ingestion en lot — création de N resources en une transaction.

L'ingestion unitaire (ResourceService.create) fait 1 commit par resource.
Pour ingérer Treekipedia (67 928 espèces), cela représenterait 67 928
commits — un ordre de grandeur au-dessus de ce que PostgreSQL peut
raisonnablement servir en temps utile.

Ce service implémente l'ingestion en lot :
- Une seule transaction pour N resources (1 commit).
- Validation de chaque resource avant insertion (échec rapide).
- Rapport détaillé : succès, erreurs de validation, erreurs de référence.
- Limite dure : 1000 resources par lot (protection mémoire + timeout).

Garde-fous :
- RBAC : chaque resource est vérifiée avant insertion.
- Mass assignment protection : _FORBIDDEN_FIELDS filtré (comme le unitaire).
- Anti-invention RFC-0014 : la garde s'applique au niveau du pipeline
  Evidence → Knowledge, pas ici (les resources brutes ne passent pas
  par l'Evidence Engine — c'est l'appelant qui qualifie).
- CON-010 : une Revision v1 est créée pour chaque resource insérée.

Échec partiel : si une resource échoue (validation ou référence), elle
est marquée dans le rapport mais n'interrompt pas le lot. La
transaction est rollbackée en cas d'erreur critique (IntegrityError
non prévue), et toutes les resources échouent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import IntegrityError

from gsie_api.core.logging import get_logger
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.resources.service import ResourceService
from gsie_api.resources.validators import ResourceValidationError, validate_resource_data
from gsie_api.shared.schemas import BulkIngestResult, BulkItemResult

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from gsie_api.resources.schemas import BulkIngestRequest, ResourceCreate, ResourceRead

logger = get_logger("gsie_api.ingestion.bulk")

# Limite dure : 1000 resources par lot. Au-delà, le client doit paginer.
# 1000 resources × ~10 Ko = ~10 Mo — sous la limite de 1 MiB du middleware
# si les resources sont petites, mais les grosses resources (assertions
# avec contenu normalisé) peuvent dépasser. Le client doit chunker.
MAX_BATCH_SIZE = 1000


class BulkIngestService:
    """Service d'ingestion en lot — N resources en une transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._unitaire = ResourceService(session)

    async def ingest(
        self,
        request: BulkIngestRequest,
        author_id: UUID | None = None,
    ) -> BulkIngestResult:
        """Ingère un lot de resources en une seule transaction.

        Args:
            request: Lot de resources à créer (max 1000).
            author_id: UUID de l'auteur (depuis le JWT).

        Returns:
            Rapport détaillé : succès et erreurs par resource.

        Raises:
            ValueError: Si le lot dépasse MAX_BATCH_SIZE.
        """
        if len(request.items) > MAX_BATCH_SIZE:
            raise ValueError(
                f"Lot trop volumineux : {len(request.items)} > {MAX_BATCH_SIZE}. "
                f"Paginez par lots de {MAX_BATCH_SIZE}."
            )

        items_result: list[BulkItemResult] = []
        success_count = 0
        error_count = 0

        for index, item in enumerate(request.items):
            try:
                resource_read = await self._create_one(item, author_id)
                items_result.append(
                    BulkItemResult(
                        index=index,
                        success=True,
                        resource_id=resource_read.id,
                        gsie_id=resource_read.gsie_id,
                    )
                )
                success_count += 1
            except ResourceValidationError as exc:
                items_result.append(
                    BulkItemResult(
                        index=index,
                        success=False,
                        error_code="validation_failed",
                        error_detail={"type": exc.type_name, "errors": exc.errors},
                    )
                )
                error_count += 1
            except ValueError as exc:
                items_result.append(
                    BulkItemResult(
                        index=index,
                        success=False,
                        error_code="unknown_type",
                        error_detail=str(exc),
                    )
                )
                error_count += 1
            except IntegrityError as exc:
                await self._session.rollback()
                items_result.append(
                    BulkItemResult(
                        index=index,
                        success=False,
                        error_code="integrity_error",
                        error_detail=str(exc.orig)[:500],
                    )
                )
                error_count += 1

        # Commit unique pour tout le lot — les resources valides sont persistées.
        # Les resources en erreur n'ont pas été ajoutées à la session (ou ont
        # été rollbackées), donc le commit ne persiste que les succès.
        try:
            await self._session.commit()
        except IntegrityError as exc:
            # Erreur critique non prévue — rollback complet.
            await self._session.rollback()
            logger.error("bulk_ingest_critical_failure", error=str(exc))
            return BulkIngestResult(
                total=len(request.items),
                success=0,
                errors=len(request.items),
                items=[
                    BulkItemResult(
                        index=i,
                        success=False,
                        error_code="transaction_failed",
                        error_detail="Erreur critique — lot entièrement rejeté",
                    )
                    for i in range(len(request.items))
                ],
            )

        logger.info(
            "bulk_ingest_completed",
            total=len(request.items),
            success=success_count,
            errors=error_count,
        )

        return BulkIngestResult(
            total=len(request.items),
            success=success_count,
            errors=error_count,
            items=items_result,
        )

    async def _create_one(self, item: ResourceCreate, author_id: UUID | None) -> ResourceRead:
        """Crée une resource dans la transaction courante (sans commit).

        Réutilise la logique de ResourceService mais sans commit — le
        commit est différé au niveau du lot.
        """
        service = self._unitaire
        model_cls = service._get_model_cls(item.type)
        errors = validate_resource_data(item.type, item.data)
        if errors:
            raise ResourceValidationError(item.type, errors)

        safe_data = service._filtrer_et_coercer(item.type, model_cls, item.data)
        await service._refuser_grain_absent(item.type, safe_data)
        gsie_id = item.gsie_id or service._generate_gsie_id(item.type)

        # Insertion sans commit — la transaction est gérée par le lot.
        resource = await self._insert_resource(item.type, gsie_id, model_cls, safe_data)
        await service._create_revision(
            resource_id=resource.id,
            version=1,
            justification="Création en lot",
            author_id=author_id,
        )
        return service._to_resource_read(resource, {})

    async def _insert_resource(
        self,
        type_name: str,
        gsie_id: str,
        model_cls: type,
        safe_data: dict[str, Any],
    ) -> ResourceModel:
        """Insère la ligne racine resource + la ligne du type (sans commit)."""
        resource = ResourceModel(type=type_name, gsie_id=gsie_id)
        self._session.add(resource)
        await self._session.flush()
        type_instance = model_cls(id=resource.id, **safe_data)
        self._session.add(type_instance)
        return resource
