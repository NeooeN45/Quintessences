"""Service de lecture du Data Registry RFC-0038.

Le service ne contacte jamais une URL de fournisseur. Il assemble uniquement
les projections persistées dans GSIE et laisse le resolver/adapters aux phases
suivantes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from sqlalchemy import and_, desc, exists, func, or_, select

from gsie_api.data.contracts import (
    DOMAIN_VOCABULARY_VERSION,
    decode_cursor,
    encode_cursor,
    filters_hash,
    validate_domain,
)
from gsie_api.data.lifecycle import transition_status
from gsie_api.data.resolver import (
    ResolutionMetadata,
    resolve_candidates,
)
from gsie_api.data.schemas import (
    CatalogResponse,
    CoverageRead,
    CoverageResponse,
    DataRightsRead,
    DatasetDetail,
    DatasetHealthRead,
    DatasetResponse,
    DatasetSummary,
    DatasetVersionRead,
    DistributionRead,
    HealthResponse,
    PageInfo,
    ProviderProjection,
    ProvidersResponse,
    ResolutionResponse,
    ResolveRequest,
    SearchCandidate,
    SearchResponse,
)
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.ecology import ScaleContextModel
from gsie_api.infrastructure.models.enums import (
    DatasetHealthStatus,
    DatasetStatus,
    EvidenceLevel,
    QualityDimension,
)
from gsie_api.infrastructure.models.governance import (
    DataRightsStatementModel,
    DatasetHealthModel,
)
from gsie_api.infrastructure.models.models_ai import (
    DataAssetModel,
    DatasetModel,
    DatasetVersionModel,
    DistributionModel,
)
from gsie_api.infrastructure.models.observation import QualityAssessmentModel
from gsie_api.infrastructure.models.prov import AgentModel, CitationModel, SourceModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class RegistryContractError(ValueError):
    """Erreur de contrat exploitable par la couche HTTP."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


_POLICY_VERSION = "registry-search-1"
_EVIDENCE_RANK = {value: rank for rank, value in enumerate(("A", "B", "C", "D", "E", "F"), start=1)}


def _json_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _safe_url(value: str | None) -> str | None:
    """Expose uniquement une URL publique sans chemin local ni présigné."""
    if not value:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    return value


def _summary(dataset: DatasetModel) -> DatasetSummary:
    return DatasetSummary(
        id=dataset.id,
        slug=dataset.slug,
        title=dataset.title,
        description=dataset.description,
        publisher_id=dataset.publisher_id,
        purpose=dataset.purpose,
        topic=dataset.topic,
        primary_domain=dataset.primary_domain,
        domains=_json_list(dataset.domains),
        tags=_json_list(dataset.tags),
        domain_vocabulary_version=dataset.domain_vocabulary_version,
    )


def _rights(rights: DataRightsStatementModel | None) -> DataRightsRead | None:
    if rights is None:
        return None
    return DataRightsRead.model_validate(rights)


def _distribution(
    distribution: DistributionModel,
    rights: DataRightsStatementModel | None = None,
) -> DistributionRead:
    return DistributionRead(
        id=distribution.id,
        dataset_version_id=distribution.dataset_version_id,
        access_method=distribution.access_method,
        access_url=_safe_url(distribution.access_url),
        licence=distribution.licence,
        data_rights_statement_id=distribution.data_rights_statement_id,
        scale_context_id=distribution.scale_context_id,
        coverage_place_id=distribution.coverage_place_id,
        format=distribution.format,
        crs=distribution.crs,
        rights=_rights(rights),
    )


def _version(
    version: DatasetVersionModel,
    distributions: Iterable[DistributionModel] = (),
    rights_by_id: dict[UUID, DataRightsStatementModel] | None = None,
) -> DatasetVersionRead:
    rights_by_id = rights_by_id or {}
    return DatasetVersionRead(
        id=version.id,
        dataset_id=version.dataset_id,
        version=version.version,
        release_date=version.release_date,
        temporal_coverage_start=version.temporal_coverage_start,
        temporal_coverage_end=version.temporal_coverage_end,
        changes=version.changes,
        schema_hash=version.schema_hash,
        stats=version.stats,
        status=version.status,
        evidence_level=version.evidence_level,
        evidence_basis=version.evidence_basis,
        evidence_assessed_at=version.evidence_assessed_at,
        distributions=[
            _distribution(
                item,
                rights_by_id[item.data_rights_statement_id]
                if item.data_rights_statement_id is not None
                else None,
            )
            for item in distributions
        ],
    )


def _apply_cursor(
    statement: Any,
    model: Any,
    token: str | None,
    expected_filters_hash: str,
) -> Any:
    if token is None:
        return statement
    try:
        payload = decode_cursor(token)
    except ValueError as exc:
        raise RegistryContractError(
            "CURSOR_INVALID", "Le curseur de pagination est invalide"
        ) from exc
    if payload.filters_hash != expected_filters_hash:
        raise RegistryContractError(
            "CURSOR_FILTER_MISMATCH", "Le curseur ne correspond pas aux filtres demandés"
        )
    return statement.where(
        or_(
            model.created_at < payload.created_at,
            and_(model.created_at == payload.created_at, model.id < payload.resource_id),
        )
    )


def _page_cursor(rows: list[Any], limit: int, request_hash: str, *, model: Any) -> str | None:
    if len(rows) <= limit:
        return None
    last = rows[limit - 1]
    if isinstance(last, tuple):
        last = next(item for item in last if hasattr(item, "created_at") and hasattr(item, "id"))
    return encode_cursor(last.created_at, last.id, filters_hash=request_hash)


class DataRegistryService:
    """Façade read-only de la base Registry."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _quality_scores(self, version_ids: list[UUID]) -> dict[UUID, float]:
        """Retourne uniquement le dernier run complet et persisté par version."""

        if not version_ids:
            return {}
        rows = list(
            (
                await self._session.execute(
                    select(QualityAssessmentModel)
                    .where(QualityAssessmentModel.target_id.in_(version_ids))
                    .order_by(desc(QualityAssessmentModel.assessed_at))
                )
            )
            .scalars()
            .all()
        )
        runs: dict[tuple[UUID, UUID], list[QualityAssessmentModel]] = {}
        order: list[tuple[UUID, UUID]] = []
        for row in rows:
            key = (row.target_id, row.assessment_run_id)
            if key not in runs:
                order.append(key)
            runs.setdefault(key, []).append(row)
        scores: dict[UUID, float] = {}
        expected = set(QualityDimension)
        for target_id, run_id in order:
            if target_id in scores:
                continue
            run = runs[(target_id, run_id)]
            if {item.dimension for item in run} != expected:
                continue
            weight_sum = sum(item.weight for item in run)
            if weight_sum <= 0:
                continue
            scores[target_id] = sum(item.score * item.weight for item in run) / weight_sum
        return scores

    async def catalog(
        self,
        *,
        cursor: str | None,
        limit: int,
        status: DatasetStatus | None = None,
        domain: str | None = None,
        publisher_id: UUID | None = None,
    ) -> CatalogResponse:
        if domain is not None:
            try:
                domain = validate_domain(domain)
            except ValueError as exc:
                raise RegistryContractError("DOMAIN_UNKNOWN", str(exc)) from exc
        request_hash = filters_hash(
            {
                "status": status.value if status else None,
                "domain": domain,
                "publisher_id": str(publisher_id) if publisher_id else None,
            }
        )
        statement = (
            select(DatasetModel)
            .join(ResourceModel, ResourceModel.id == DatasetModel.id)
            .where(ResourceModel.deleted_at.is_(None))
        )
        if status is not None:
            statement = statement.where(
                exists(
                    select(DatasetVersionModel.id).where(
                        DatasetVersionModel.dataset_id == DatasetModel.id,
                        DatasetVersionModel.status == status,
                    )
                )
            )
        if domain is not None:
            statement = statement.where(
                or_(DatasetModel.primary_domain == domain, DatasetModel.domains.contains([domain]))
            )
        if publisher_id is not None:
            statement = statement.where(DatasetModel.publisher_id == publisher_id)
        statement = _apply_cursor(statement, DatasetModel, cursor, request_hash)
        statement = statement.order_by(desc(DatasetModel.created_at), desc(DatasetModel.id)).limit(
            limit + 1
        )
        rows = list((await self._session.execute(statement)).scalars().all())
        page_rows = rows[:limit]
        return CatalogResponse(
            items=[_summary(item) for item in page_rows],
            page=PageInfo(
                limit=limit,
                next_cursor=_page_cursor(rows, limit, request_hash, model=DatasetModel),
            ),
        )

    async def dataset(self, dataset_id: UUID) -> DatasetResponse | None:
        statement = (
            select(DatasetModel)
            .join(ResourceModel, ResourceModel.id == DatasetModel.id)
            .where(DatasetModel.id == dataset_id, ResourceModel.deleted_at.is_(None))
        )
        dataset = (await self._session.execute(statement)).scalar_one_or_none()
        if dataset is None:
            return None
        versions = list(
            (
                await self._session.execute(
                    select(DatasetVersionModel)
                    .where(DatasetVersionModel.dataset_id == dataset_id)
                    .order_by(desc(DatasetVersionModel.created_at), desc(DatasetVersionModel.id))
                )
            )
            .scalars()
            .all()
        )
        version_ids = [item.id for item in versions]
        distributions = (
            list(
                (
                    await self._session.execute(
                        select(DistributionModel).where(
                            DistributionModel.dataset_version_id.in_(version_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            if version_ids
            else []
        )
        rights_ids = {
            item.data_rights_statement_id for item in distributions if item.data_rights_statement_id
        }
        rights = (
            list(
                (
                    await self._session.execute(
                        select(DataRightsStatementModel).where(
                            DataRightsStatementModel.id.in_(rights_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            if rights_ids
            else []
        )
        rights_by_id = {item.id: item for item in rights}
        by_version: dict[UUID, list[DistributionModel]] = {}
        for item in distributions:
            by_version.setdefault(item.dataset_version_id, []).append(item)
        return DatasetResponse(
            item=DatasetDetail(
                dataset=_summary(dataset),
                versions=[
                    _version(item, by_version.get(item.id, []), rights_by_id) for item in versions
                ],
            )
        )

    async def providers(
        self,
        *,
        cursor: str | None,
        limit: int,
        dataset_id: UUID | None,
        include_agent: bool,
    ) -> ProvidersResponse:
        request_hash = filters_hash({"dataset_id": str(dataset_id) if dataset_id else None})
        target_dataset = (
            select(
                DatasetModel.id.label("dataset_id"),
                DatasetModel.id.label("target_id"),
                DatasetModel.publisher_id,
            )
            .union_all(
                select(
                    DatasetVersionModel.dataset_id.label("dataset_id"),
                    DatasetVersionModel.id.label("target_id"),
                    DatasetModel.publisher_id,
                ).join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
            )
            .subquery()
        )
        statement = (
            select(CitationModel, SourceModel, target_dataset.c.dataset_id, AgentModel)
            .join(SourceModel, SourceModel.id == CitationModel.source_id)
            .join(target_dataset, target_dataset.c.target_id == CitationModel.target_id)
            .outerjoin(AgentModel, AgentModel.id == target_dataset.c.publisher_id)
        )
        if dataset_id is not None:
            statement = statement.where(target_dataset.c.dataset_id == dataset_id)
        statement = statement.where(ResourceModel.deleted_at.is_(None))
        # ResourceModel est jointe explicitement sur la citation afin de ne pas
        # exposer une ressource soft-deleted. Agent est masqué si le rôle ne
        # permet pas la lecture de données identifiantes.
        statement = statement.join(ResourceModel, ResourceModel.id == CitationModel.id)
        statement = _apply_cursor(statement, CitationModel, cursor, request_hash)
        statement = statement.order_by(
            desc(CitationModel.created_at), desc(CitationModel.id)
        ).limit(limit + 1)
        rows = list((await self._session.execute(statement)).all())
        page_rows = rows[:limit]
        items: list[ProviderProjection] = []
        for citation, source, target_dataset_id, agent in page_rows:
            items.append(
                ProviderProjection(
                    agent_id=agent.id if include_agent and agent else None,
                    agent_name=agent.name if include_agent and agent else None,
                    agent_type=agent.type if include_agent and agent else None,
                    source_id=source.id,
                    source_title=source.title,
                    source_subtype=source.subtype,
                    source_nature=source.source_nature,
                    source_url=_safe_url(source.url),
                    citation_role=citation.citation_role,
                    dataset_id=target_dataset_id,
                )
            )
        return ProvidersResponse(
            items=items,
            page=PageInfo(
                limit=limit,
                next_cursor=_page_cursor(rows, limit, request_hash, model=CitationModel),
            ),
        )

    async def health(
        self,
        *,
        cursor: str | None,
        limit: int,
        health_status: DatasetHealthStatus | None,
        dataset_version_id: UUID | None,
        distribution_id: UUID | None,
    ) -> HealthResponse:
        request_hash = filters_hash(
            {
                "health_status": health_status.value if health_status else None,
                "dataset_version_id": str(dataset_version_id) if dataset_version_id else None,
                "distribution_id": str(distribution_id) if distribution_id else None,
            }
        )
        statement = select(DatasetHealthModel)
        if health_status is not None:
            statement = statement.where(DatasetHealthModel.health_status == health_status)
        if dataset_version_id is not None:
            statement = statement.where(DatasetHealthModel.dataset_version_id == dataset_version_id)
        if distribution_id is not None:
            statement = statement.where(DatasetHealthModel.distribution_id == distribution_id)
        statement = _apply_cursor(statement, DatasetHealthModel, cursor, request_hash)
        statement = statement.order_by(
            desc(DatasetHealthModel.created_at), desc(DatasetHealthModel.id)
        ).limit(limit + 1)
        rows = list((await self._session.execute(statement)).scalars().all())
        return HealthResponse(
            items=[DatasetHealthRead.model_validate(item) for item in rows[:limit]],
            page=PageInfo(
                limit=limit,
                next_cursor=_page_cursor(rows, limit, request_hash, model=DatasetHealthModel),
            ),
        )

    async def coverage(self, *, cursor: str | None, limit: int) -> CoverageResponse:
        request_hash = filters_hash({})
        statement = (
            select(DistributionModel, PlaceModel, ScaleContextModel)
            .outerjoin(PlaceModel, PlaceModel.id == DistributionModel.coverage_place_id)
            .outerjoin(
                ScaleContextModel, ScaleContextModel.id == DistributionModel.scale_context_id
            )
        )
        statement = _apply_cursor(statement, DistributionModel, cursor, request_hash)
        statement = statement.order_by(
            desc(DistributionModel.created_at), desc(DistributionModel.id)
        ).limit(limit + 1)
        rows = list((await self._session.execute(statement)).all())
        items = [
            CoverageRead(
                distribution_id=distribution.id,
                dataset_version_id=distribution.dataset_version_id,
                coverage_place_id=distribution.coverage_place_id,
                place_label=place.label if place else None,
                area_m2=place.area_m2 if place else None,
                crs=distribution.crs,
                scale_context_id=distribution.scale_context_id,
                grain_m2=scale.grain_m2 if scale else None,
                extent_m2=scale.extent_m2 if scale else None,
            )
            for distribution, place, scale in rows[:limit]
        ]
        return CoverageResponse(
            items=items,
            page=PageInfo(
                limit=limit,
                next_cursor=_page_cursor(rows, limit, request_hash, model=DistributionModel),
            ),
        )

    async def search(self, query: Any, *, include_blocked: bool = False) -> SearchResponse:
        """Recherche catalogue ; le resolver peut demander les bloqués."""
        request_hash = filters_hash(query.model_dump(mode="json", exclude={"cursor", "limit"}))
        statement = (
            select(DatasetVersionModel, DatasetModel)
            .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
            .join(ResourceModel, ResourceModel.id == DatasetVersionModel.id)
            .where(ResourceModel.deleted_at.is_(None))
        )
        if query.theme:
            statement = statement.where(
                or_(
                    DatasetModel.primary_domain == query.theme,
                    DatasetModel.domains.contains([query.theme]),
                )
            )
        if query.date_start is not None:
            statement = statement.where(
                DatasetVersionModel.temporal_coverage_end.is_not(None),
                DatasetVersionModel.temporal_coverage_end >= query.date_start,
            )
        if query.date_end is not None:
            statement = statement.where(
                DatasetVersionModel.temporal_coverage_start.is_not(None),
                DatasetVersionModel.temporal_coverage_start <= query.date_end,
            )
        if query.max_grain_m2 is not None:
            statement = statement.where(
                exists(
                    select(DistributionModel.id)
                    .join(
                        ScaleContextModel,
                        ScaleContextModel.id == DistributionModel.scale_context_id,
                    )
                    .where(
                        DistributionModel.dataset_version_id == DatasetVersionModel.id,
                        ScaleContextModel.grain_m2.is_not(None),
                        ScaleContextModel.grain_m2 <= query.max_grain_m2,
                    )
                )
            )
        if query.bbox is not None:
            min_lon, min_lat, max_lon, max_lat = query.bbox
            bbox_geometry = func.ST_MakeEnvelope(
                min_lon,
                min_lat,
                max_lon,
                max_lat,
                4326,
            )
            statement = statement.where(
                exists(
                    select(DistributionModel.id)
                    .join(PlaceModel, PlaceModel.id == DistributionModel.coverage_place_id)
                    .where(
                        DistributionModel.dataset_version_id == DatasetVersionModel.id,
                        PlaceModel.geom_4326.is_not(None),
                        func.ST_Intersects(PlaceModel.geom_4326, bbox_geometry),
                    )
                )
            )
        if not include_blocked and query.use == "inference":
            statement = statement.where(DatasetVersionModel.status == DatasetStatus.production)
        elif not include_blocked:
            statement = statement.where(
                DatasetVersionModel.status.not_in(
                    {DatasetStatus.archived, DatasetStatus.broken, DatasetStatus.unavailable}
                )
            )
        if not include_blocked and query.minimum_evidence_level is not None:
            accepted = [
                level
                for level in EvidenceLevel
                if _EVIDENCE_RANK[level.value] <= _EVIDENCE_RANK[query.minimum_evidence_level.value]
            ]
            statement = statement.where(DatasetVersionModel.evidence_level.in_(accepted))
        statement = _apply_cursor(statement, DatasetVersionModel, query.cursor, request_hash)
        statement = statement.order_by(
            desc(DatasetVersionModel.created_at), desc(DatasetVersionModel.id)
        ).limit(query.limit + 1)
        rows = list((await self._session.execute(statement)).all())
        quality_scores = (
            await self._quality_scores([version.id for version, _dataset in rows[: query.limit]])
            if query.minimum_quality_score is not None
            else {}
        )
        candidates: list[SearchCandidate] = []
        for version, dataset in rows[: query.limit]:
            distributions = list(
                (
                    await self._session.execute(
                        select(DistributionModel).where(
                            DistributionModel.dataset_version_id == version.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            rights_ids = {
                item.data_rights_statement_id
                for item in distributions
                if item.data_rights_statement_id
            }
            rights = (
                list(
                    (
                        await self._session.execute(
                            select(DataRightsStatementModel).where(
                                DataRightsStatementModel.id.in_(rights_ids)
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if rights_ids
                else []
            )
            rights_by_id = {item.id: item for item in rights}
            reasons: list[str] = []
            status_value = (
                version.status.value
                if isinstance(version.status, DatasetStatus)
                else str(version.status)
            )
            if (
                include_blocked
                and query.use == "inference"
                and status_value != DatasetStatus.production.value
            ):
                reasons.append("STATUS_NOT_PRODUCTION")
            elif (
                include_blocked
                and query.use == "display"
                and status_value
                in {
                    DatasetStatus.archived.value,
                    DatasetStatus.broken.value,
                    DatasetStatus.unavailable.value,
                }
            ):
                reasons.append("STATUS_NOT_AVAILABLE")
            if include_blocked and query.minimum_evidence_level is not None:
                if version.evidence_level is None:
                    reasons.append("EVIDENCE_MISSING")
                elif (
                    _EVIDENCE_RANK[version.evidence_level.value]
                    > _EVIDENCE_RANK[query.minimum_evidence_level.value]
                ):
                    reasons.append("EVIDENCE_INSUFFICIENT")
            if include_blocked and query.use == "inference" and version.evidence_level is None:
                reasons.append("EVIDENCE_MISSING")
            if query.commercial_use_required and not any(
                item.data_rights_statement_id is not None
                and rights_by_id.get(item.data_rights_statement_id) is not None
                and rights_by_id[item.data_rights_statement_id].commercial_use_allowed
                for item in distributions
            ):
                reasons.append("COMMERCIAL_USE_NOT_ALLOWED")
            if query.minimum_quality_score is not None:
                quality_score = quality_scores.get(version.id)
                if quality_score is None:
                    reasons.append("QUALITY_MISSING")
                elif quality_score < query.minimum_quality_score:
                    reasons.append("QUALITY_BELOW_MINIMUM")
            if query.use == "inference":
                assets = list(
                    (
                        await self._session.execute(
                            select(DataAssetModel).where(
                                DataAssetModel.dataset_version_id == version.id,
                                DataAssetModel.storage_uri.is_not(None),
                                DataAssetModel.checksum.is_not(None),
                                DataAssetModel.archived_at.is_not(None),
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if not assets:
                    reasons.append("ASSET_NOT_ARCHIVED")
            candidates.append(
                SearchCandidate(
                    dataset=_summary(dataset),
                    version=_version(version, distributions, rights_by_id),
                    blocking_reasons=reasons,
                )
            )
        return SearchResponse(
            items=candidates,
            page=PageInfo(
                limit=query.limit,
                next_cursor=_page_cursor(
                    rows, query.limit, request_hash, model=DatasetVersionModel
                ),
            ),
            policy_version=_POLICY_VERSION,
        )

    async def resolve(
        self,
        query: ResolveRequest,
        *,
        trace_id: str | None,
    ) -> ResolutionResponse:
        """Résout une requête avec la même politique pour le fallback."""

        search_response = await self.search(query, include_blocked=True)
        metadata: dict[UUID, ResolutionMetadata] = {}
        version_ids = [item.version.id for item in search_response.items]
        if version_ids and (query.minimum_quality_score is not None or "quality" in query.prefer):
            for version_id, quality_score in (await self._quality_scores(version_ids)).items():
                current = metadata.get(version_id, ResolutionMetadata())
                metadata[version_id] = ResolutionMetadata(
                    quality_score=quality_score,
                    freshness_at=current.freshness_at,
                    offline_available=current.offline_available,
                )
        if version_ids and (query.use == "inference" or "offline_availability" in query.prefer):
            assets = list(
                (
                    await self._session.execute(
                        select(DataAssetModel).where(
                            DataAssetModel.dataset_version_id.in_(version_ids),
                            DataAssetModel.storage_uri.is_not(None),
                            DataAssetModel.checksum.is_not(None),
                            DataAssetModel.archived_at.is_not(None),
                        )
                    )
                )
                .scalars()
                .all()
            )
            archived_versions = {item.dataset_version_id for item in assets}
            for version_id in version_ids:
                metadata[version_id] = ResolutionMetadata(
                    quality_score=None,
                    offline_available=version_id in archived_versions,
                )
        if version_ids and "freshness" in query.prefer:
            health_rows = list(
                (
                    await self._session.execute(
                        select(DatasetHealthModel)
                        .where(DatasetHealthModel.dataset_version_id.in_(version_ids))
                        .order_by(desc(DatasetHealthModel.checked_at))
                    )
                )
                .scalars()
                .all()
            )
            for health in health_rows:
                if health.dataset_version_id not in metadata:
                    metadata[health.dataset_version_id] = ResolutionMetadata()
                current = metadata[health.dataset_version_id]
                if current.freshness_at is None:
                    metadata[health.dataset_version_id] = ResolutionMetadata(
                        quality_score=current.quality_score,
                        freshness_at=health.last_modified or health.checked_at,
                        offline_available=current.offline_available,
                    )
        return resolve_candidates(
            query,
            search_response.items,
            metadata=metadata,
            trace_id=trace_id,
            vocabulary_version=DOMAIN_VOCABULARY_VERSION,
        )

    @staticmethod
    def validate_status_transition(
        current: DatasetStatus | str, target: DatasetStatus | str
    ) -> DatasetStatus:
        """Porte interne pour les écritures de cycle de vie à venir."""
        return transition_status(current, target)
