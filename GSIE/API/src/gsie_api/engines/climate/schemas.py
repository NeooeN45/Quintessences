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

from datetime import date, datetime
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


class DangerFeuxDepartement(BaseModel):
    """Niveau de danger de feux de forêt réel d'un département (Météo des forêts)."""

    model_config = ConfigDict(extra="forbid")

    dep_code: str
    dep_nom: str
    niveau_j1: int
    niveau_j2: int
    reference_time: datetime
    source: SourceReference


class ClimatologieQuotidienneQuery(BaseModel):
    """Requête de données climatologiques quotidiennes réelles pour une station DPClim.

    id_station : identifiant de poste Météo-France (8 chiffres, ex.
    33042001), obtenu via GET /climate/climatologie-stations. Différent
    de l'identifiant OMM 5 chiffres utilisé par ClimateQuery (SYNOP).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    id_station: str = Field(min_length=8, max_length=8)
    date_deb_periode: datetime
    date_fin_periode: datetime


class ObservationClimatologiqueQuotidienne(BaseModel):
    """Une ligne réelle du produit quotidien DPClim (Météo-France).

    Le jeu de colonnes du CSV varie selon la station (vérifié
    manuellement le 2026-07-18 : certaines stations exposent NEIGETOTX/
    NEIGETOT06, d'autres seulement NEIGETOT) — modéliser les ~130
    colonnes en champs fixes perdrait ou casserait selon la station.
    `valeurs_brutes` conserve donc CHAQUE colonne reçue verbatim (nom de
    colonne -> valeur brute, chaîne vide -> None), sans perte, en plus
    de quelques champs pratiques typés pour les variables les plus
    utilisées. Les codes qualité (Q*) sont conservés bruts dans
    `valeurs_brutes` — leur interprétation nécessite la documentation
    officielle Météo-France, non vérifiée ici (ADR-007 : pas de sens
    inventé).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    id_station: str
    date: date
    rr_mm: float | None = None
    tn_c: float | None = None
    tx_c: float | None = None
    tm_c: float | None = None
    valeurs_brutes: dict[str, str | None]
    source: SourceReference


class VigilancePhenomene(BaseModel):
    """Un phénomène de vigilance sur un domaine (code brut Météo-France, ADR-007)."""

    model_config = ConfigDict(extra="forbid")

    phenomenon_id: str
    color_id: int


class VigilanceDomaine(BaseModel):
    """Niveau de vigilance réel d'un domaine (département/zone) pour une échéance."""

    model_config = ConfigDict(extra="forbid")

    domain_id: str
    max_color_id: int
    phenomenes: list[VigilancePhenomene]


class VigilanceBulletin(BaseModel):
    """Carte de vigilance réelle pour une échéance (J ou J+1)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    echeance: str
    update_time: datetime
    domaines: list[VigilanceDomaine]
    source: SourceReference


class ObservationHoraireDepartement(BaseModel):
    """Une observation horaire réelle d'une station (Package Observations, 24h glissantes)."""

    model_config = ConfigDict(extra="forbid")

    geo_id_insee: str
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


class AromeTemperatureQuery(BaseModel):
    """Requête de température 2 m réelle du modèle AROME pour un point et une échéance."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    latitude: float = Field(ge=37.5, le=55.4, description="Domaine réel du service AROME France")
    longitude: float = Field(ge=-12.0, le=16.0, description="Domaine réel du service AROME France")
    echeance: datetime = Field(
        description="Instant UTC souhaité (doit être dans le run le plus récent)"
    )


class AromeTemperatureResult(BaseModel):
    """Température 2 m réelle du modèle AROME (décodée depuis un GRIB2 réel)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    latitude: float
    longitude: float
    echeance: datetime
    temperature_c: float
    run_modele: str = Field(description="Identifiant de couverture WCS (run de modèle utilisé)")
    resolution_deg: float = Field(default=0.01, description="Résolution native AROME France")
    source: SourceReference
