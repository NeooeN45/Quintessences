"""WebSocket events — définition des events temps réel pour le Hub.

Le Hub (Unreal Engine 5.8) se connecte en WebSocket et reçoit des events
sur des canaux. Redis Pub/Sub assure le fan-out vers les clients connectés.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class EventType(StrEnum):
    """Types d'events diffusés sur le WebSocket."""

    resource_created = "resource.created"
    resource_updated = "resource.updated"
    resource_deleted = "resource.deleted"
    phenomenon_detected = "phenomenon.detected"
    model_completed = "model.completed"
    recommendation_ready = "recommendation.ready"
    alert_fire_risk = "alert.fire_risk"
    alert_drought = "alert.drought"
    alert_storm = "alert.storm"
    alert_pest = "alert.pest"
    observation_received = "observation.received"
    assertion_validated = "assertion.validated"
    correlation_detected = "correlation.detected"


class WSEvent(BaseModel):
    """Event diffusé sur le WebSocket."""

    event_type: EventType
    resource_id: UUID | None = None
    resource_type: str | None = None
    data: dict[str, Any]
    timestamp: str
    trace_id: str | None = None
