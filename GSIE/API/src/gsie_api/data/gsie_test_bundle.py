"""Import contrôlé des bundles Forge dans GSIE TEST uniquement."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5  # noqa: TC003

from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from shapely import wkt
from shapely.errors import ShapelyError
from sqlalchemy import select

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.knowledge.schemas import (
    DomaineScientifique,
    DomaineValidite,
    KnowledgeIngestRequest,
    KnowledgeType,
)
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.enums import CitationRole, SourceNature, SourceSubtype
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel
from gsie_api.infrastructure.models.prov import CitationModel, SourceModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_SUPPORTED_SRID = 2154
_SOURCE_STORAGE: dict[str, tuple[SourceSubtype, SourceNature]] = {
    "peer_reviewed": (SourceSubtype.publication, SourceNature.knowledge_provider),
    "referentiel_officiel": (SourceSubtype.publication, SourceNature.reference),
    "expert_identifie": (SourceSubtype.expert_statement, SourceNature.expert_statement),
    "observation_terrain": (SourceSubtype.dataset, SourceNature.data_provider),
}


class SourceReferencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type_source: SourceType
    auteur: str = Field(min_length=1, max_length=300)
    date_publication: str = Field(min_length=1, max_length=50)
    reference: str = Field(min_length=1, max_length=500)


class PlacePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1, max_length=300)
    srid: int = Field(gt=0)
    geometry_wkt: str = Field(min_length=1, max_length=2_000_000)
    source: SourceReferencePayload

    @field_validator("srid")
    @classmethod
    def require_supported_srid(cls, value: int) -> int:
        if value != _SUPPORTED_SRID:
            raise ValueError(f"SRID non supporté : {value} ; attendu {_SUPPORTED_SRID}")
        return value

    @field_validator("geometry_wkt")
    @classmethod
    def require_valid_geometry(cls, value: str) -> str:
        try:
            geometry = wkt.loads(value)
        except ShapelyError as exc:
            raise ValueError("geometry_wkt doit être un WKT valide") from exc
        if geometry.is_empty or not geometry.is_valid:
            raise ValueError("geometry_wkt doit être une géométrie non vide et valide")
        return value


class StationObservationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_type: str = Field(min_length=1, max_length=100)
    value: float | str | bool
    unit: str = Field(min_length=1, max_length=30)
    method_id: str = Field(min_length=1, max_length=150)
    method_version: str = Field(min_length=1, max_length=50)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at doit être horodaté avec un fuseau")
        return value.astimezone(UTC)


class QualifiedRulePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    connaissance_id: UUID
    type: Literal["regle", "seuil"]
    titre: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=5000)
    domaine_scientifique: str = Field(min_length=1, max_length=100)
    contenu_normalise: dict[str, Any] = Field(min_length=1)
    evidence_level: EvidenceLevel
    source: SourceReferencePayload
    statut: Literal["accepted"]
    qualificateurs: dict[str, str] = Field(min_length=1, max_length=20)
    domaines_validite: list[DomaineValidite] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def require_qualification(self) -> QualifiedRulePayload:
        required = {
            "variable",
            "operateur",
            "valeur",
            "enonce_conclusion",
            "niveau_confiance",
            "role",
        }
        missing = sorted(required - self.qualificateurs.keys())
        if missing:
            raise ValueError(f"qualificateur(s) requis absent(s) : {missing}")
        return self


class GlobalStatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["global_state.v0.1"]
    etat: Literal["sain", "vigueur_reduite", "deperissement", "critique"]
    justification: str = Field(min_length=1, max_length=1000)
    evidence_level: EvidenceLevel
    observed_at: datetime
    source: SourceReferencePayload

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at doit être horodaté avec un fuseau")
        return value.astimezone(UTC)


class GsiePreparationBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["gsie_test_preparation.v0.1"]
    bundle_id: UUID
    station_id: UUID
    submitted_by: UUID
    generated_at: datetime
    place: PlacePayload
    observations: list[StationObservationPayload] = Field(min_length=1, max_length=500)
    rules: list[QualifiedRulePayload] = Field(min_length=1, max_length=500)
    etat_global: GlobalStatePayload

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("generated_at doit être horodaté avec un fuseau")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_unique_rules(self) -> GsiePreparationBundle:
        ids = [rule.connaissance_id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("les règles du bundle doivent avoir des identifiants uniques")
        return self


class GsieTestBundleImportError(ValueError):
    """Le bundle ne peut pas être appliqué à GSIE TEST."""


class GsieTestBundleImporter:
    """Applique un bundle Forge validé dans une base explicitement de test."""

    def __init__(self, session: AsyncSession, *, database_role: str) -> None:
        self._session = session
        self._database_role = database_role

    async def import_bundle(self, bundle: GsiePreparationBundle) -> None:
        if self._database_role != "test":
            raise GsieTestBundleImportError(
                "import GSIE TEST refusé : database_role doit être 'test'"
            )
        await self._ensure_resources_absent(bundle)
        await self._create_place(bundle)
        await self._ingest_rules(bundle)
        self._create_accepted_intake(bundle)
        await self._session.flush()

    async def _ensure_resources_absent(self, bundle: GsiePreparationBundle) -> None:
        identifiers = [bundle.station_id, *(rule.connaissance_id for rule in bundle.rules)]
        existing = (
            (
                await self._session.execute(
                    select(ResourceModel.id).where(ResourceModel.id.in_(identifiers))
                )
            )
            .scalars()
            .all()
        )
        if not existing:
            return
        if bundle.station_id in existing:
            raise GsieTestBundleImportError(
                f"station {bundle.station_id} déjà présente : bundle non idempotent"
            )
        raise GsieTestBundleImportError(
            f"connaissance déjà présente : {', '.join(str(identifier) for identifier in existing)}"
        )

    async def _create_place(self, bundle: GsiePreparationBundle) -> None:
        existing = await self._session.get(ResourceModel, bundle.station_id)
        if existing is not None:
            raise GsieTestBundleImportError(
                f"station {bundle.station_id} déjà présente : bundle non idempotent"
            )
        self._session.add(
            ResourceModel(
                id=bundle.station_id,
                type="place",
                gsie_id=f"gsie:place:{bundle.station_id}",
                metadata_json={"source": bundle.place.source.model_dump(mode="json")},
            )
        )
        await self._session.flush()
        self._session.add(
            PlaceModel(
                id=bundle.station_id,
                geometry=WKTElement(bundle.place.geometry_wkt, srid=bundle.place.srid),
                srid=bundle.place.srid,
                label=bundle.place.label,
                area_m2=None,
            )
        )

    async def _ingest_rules(self, bundle: GsiePreparationBundle) -> None:
        engine = KnowledgeEngine(self._session)
        source_ids: dict[str, UUID] = {}
        for rule in bundle.rules:
            source_key = _source_key(rule.source)
            source_id = source_ids.get(source_key)
            if source_id is None:
                source_id = await self._create_source(bundle, rule.source)
                source_ids[source_key] = source_id
            await engine.ingest(
                KnowledgeIngestRequest(
                    connaissance_id=rule.connaissance_id,
                    contenu_normalise=rule.contenu_normalise,
                    type=KnowledgeType(rule.type),
                    titre=rule.titre,
                    description=rule.description,
                    domaine_scientifique=DomaineScientifique(rule.domaine_scientifique),
                    evidence_level=EvidenceLevel(rule.evidence_level),
                    source=SourceReference.model_validate(rule.source.model_dump()),
                    statut="accepte",
                    domaines_validite=[
                        DomaineValidite.model_validate(item) for item in rule.domaines_validite
                    ],
                    moteurs_consommateurs=["reasoning", "diagnostic"],
                    qualificateurs=rule.qualificateurs,
                    spatial_scope_id=bundle.station_id,
                )
            )
            await self._create_citation(bundle, rule.connaissance_id, source_id)

    async def _create_source(
        self, bundle: GsiePreparationBundle, source: SourceReferencePayload
    ) -> UUID:
        source_id = uuid5(
            NAMESPACE_URL,
            f"gsie-test-source:{bundle.bundle_id}:{_source_key(source)}",
        )
        subtype, nature = _SOURCE_STORAGE[source.type_source.value]
        metadata = {
            "bundle_id": str(bundle.bundle_id),
            "source": source.model_dump(mode="json"),
        }
        self._session.add(
            ResourceModel(
                id=source_id,
                type="source",
                gsie_id=f"gsie:test:source:{source_id}",
                metadata_json=metadata,
            )
        )
        await self._session.flush()
        self._session.add(
            SourceModel(
                id=source_id,
                title=source.reference,
                subtype=subtype,
                source_nature=nature,
                auteur=source.auteur,
                date_publication=source.date_publication,
                url=_reference_url(source.reference),
            )
        )
        await self._session.flush()
        return source_id

    async def _create_citation(
        self, bundle: GsiePreparationBundle, target_id: UUID, source_id: UUID
    ) -> None:
        citation_id = uuid5(
            NAMESPACE_URL,
            f"gsie-test-citation:{bundle.bundle_id}:{target_id}",
        )
        self._session.add(
            ResourceModel(
                id=citation_id,
                type="citation",
                gsie_id=f"gsie:test:citation:{citation_id}",
                metadata_json={"bundle_id": str(bundle.bundle_id)},
            )
        )
        await self._session.flush()
        self._session.add(
            CitationModel(
                id=citation_id,
                source_id=source_id,
                target_id=target_id,
                citation_role=CitationRole.primary,
            )
        )

    def _create_accepted_intake(self, bundle: GsiePreparationBundle) -> None:
        state = bundle.etat_global.model_dump(mode="json")
        station = {
            "schema_version": "station_intake.v0.1",
            "context": {"station_id": str(bundle.station_id), "source": "Forge"},
            "observations": [
                observation.model_dump(mode="json") for observation in bundle.observations
            ],
            "calculations": [],
            "interpretations": [],
            "recommendations": [],
            "provenance": {"bundle_id": str(bundle.bundle_id)},
        }
        payload = {"station": station, "etat_global": state}
        self._session.add(
            FieldIntakeModel(
                submitted_by=bundle.submitted_by,
                application_key="forge-gsie-test",
                client_event_id=str(bundle.bundle_id),
                kind="observation",
                observed_at=bundle.etat_global.observed_at.astimezone(UTC),
                status="accepted",
                payload=payload,
                provenance={
                    "bundle_id": str(bundle.bundle_id),
                    "bundle_schema_version": bundle.schema_version,
                    "bundle_hash": _sha256_json(bundle.model_dump(mode="json")),
                    "source": bundle.etat_global.source.model_dump(mode="json"),
                },
                payload_hash=_sha256_json(payload),
                target_resource_id=bundle.station_id,
            )
        )


def _sha256_json(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _source_key(source: SourceReferencePayload) -> str:
    return "|".join(
        (
            source.type_source.value,
            source.auteur,
            source.date_publication,
            source.reference,
        )
    )


def _reference_url(reference: str) -> str | None:
    return reference if reference.startswith(("https://", "http://")) else None


__all__ = [
    "GsiePreparationBundle",
    "GsieTestBundleImportError",
    "GsieTestBundleImporter",
]
