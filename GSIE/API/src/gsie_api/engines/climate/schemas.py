"""Schémas Pydantic pour le Climate Engine.

Périmètre v1 : dernière observation SYNOP réelle (Météo-France, licence
ouverte 2.0, aucune clé requise) pour une station donnée — température,
humidité, pression, vent, précipitations. Pas de projection climatique
(DRIAS/RCP) ni de réanalyse en v1 — hors périmètre, RFC-0014 pour la
suite (nécessitera la clé du portail API Météo-France, AROME/DRIAS).

Une valeur SYNOP absente (champ vide dans le CSV, capteur manquant ou
paramètre non mesuré à cette station) est omise du résultat, jamais
remplacée par une valeur par défaut (ADR-007).
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.evidence.schemas import SourceReference


class ClimateQuery(BaseModel):
    """Requête de dernière observation pour une station SYNOP."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    station_id: str = Field(
        min_length=5, max_length=5, description="Identifiant OMM à 5 chiffres (ex. 07510)"
    )


class ObservationClimatique(BaseModel):
    """Dernière observation réelle d'une station SYNOP (Météo-France)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    station_id: str
    nom_station: str
    latitude: float
    longitude: float
    date_observation: datetime
    temperature_c: float | None = None
    humidite_pct: float | None = None
    pression_hpa: float | None = None
    vent_direction_deg: float | None = None
    vent_vitesse_ms: float | None = None
    precipitations_1h_mm: float | None = None
    source: SourceReference
