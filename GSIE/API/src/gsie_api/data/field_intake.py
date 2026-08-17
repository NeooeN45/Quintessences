"""Contrat et service d'intake des observations applicatives en quarantaine."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from gsie_api.data.field_intake_station import StationIntake  # noqa: TC001
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel

FieldIntakeKind = Literal["observation", "feedback", "action_outcome", "correction"]


class FieldIntakeSubmission(BaseModel):
    """Payload signé logiquement par l'application, sans statut canonique."""

    model_config = ConfigDict(extra="forbid")

    application_key: str = Field(min_length=1, max_length=100)
    client_event_id: str = Field(min_length=1, max_length=200)
    kind: FieldIntakeKind
    observed_at: datetime
    payload: dict[str, Any] = Field(min_length=1, max_length=100)
    provenance: dict[str, Any] = Field(min_length=1, max_length=50)
    target_resource_id: UUID | None = None
    station: StationIntake | None = None

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at doit être horodaté avec un fuseau")
        return value.astimezone(UTC)


class FieldIntakeResponse(BaseModel):
    """Résultat stable d'une réception en quarantaine."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: Literal["quarantined"]
    duplicate: bool
    payload_hash: str


class FieldIntakeConflict(ValueError):  # noqa: N818 - nom public historique du contrat API
    """Le même événement client a été soumis avec des données différentes."""


class FieldIntakeService:
    """Persistе les soumissions sans créer ni modifier une ressource canonique."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def submit(
        self,
        submission: FieldIntakeSubmission,
        *,
        submitted_by: UUID,
        application_version: str,
        trace_id: str,
    ) -> FieldIntakeResponse:
        payload_hash = _payload_hash(submission)
        existing = await self._find_existing(submission)
        if existing is not None:
            if existing.payload_hash != payload_hash:
                raise FieldIntakeConflict("client_event_id déjà utilisé avec un payload différent")
            return FieldIntakeResponse(
                id=existing.id,
                status="quarantined",
                duplicate=True,
                payload_hash=payload_hash,
            )

        provenance = {
            **submission.provenance,
            "application_key": submission.application_key,
            "application_version": application_version,
            "submitted_by": str(submitted_by),
            "trace_id": trace_id,
            "received_at": datetime.now(UTC).isoformat(),
        }
        stored_payload = dict(submission.payload)
        if submission.station is not None:
            stored_payload["station"] = submission.station.model_dump(mode="json")
        intake = FieldIntakeModel(
            submitted_by=submitted_by,
            application_key=submission.application_key,
            client_event_id=submission.client_event_id,
            kind=submission.kind,
            observed_at=submission.observed_at,
            status="quarantined",
            payload=stored_payload,
            provenance=provenance,
            payload_hash=payload_hash,
            target_resource_id=submission.target_resource_id,
        )
        self._session.add(intake)
        await self._session.flush()
        return FieldIntakeResponse(
            id=intake.id,
            status="quarantined",
            duplicate=False,
            payload_hash=payload_hash,
        )

    async def _find_existing(self, submission: FieldIntakeSubmission) -> FieldIntakeModel | None:
        statement = select(FieldIntakeModel).where(
            FieldIntakeModel.application_key == submission.application_key,
            FieldIntakeModel.client_event_id == submission.client_event_id,
        )
        return (await self._session.execute(statement)).scalar_one_or_none()


def _submitted_by(subject: object) -> UUID:
    try:
        return UUID(str(subject))
    except (ValueError, TypeError, AttributeError):
        return uuid5(NAMESPACE_URL, f"gsie:field-intake:{subject}")


def _payload_hash(submission: FieldIntakeSubmission) -> str:
    canonical = submission.model_dump(mode="json", exclude={"target_resource_id"})
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "FieldIntakeConflict",
    "FieldIntakeResponse",
    "FieldIntakeService",
    "FieldIntakeSubmission",
    "_submitted_by",
]
