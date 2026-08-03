"""Schémas Pydantic pour le Climate Engine.

Périmètre v1 : dernière observation SYNOP réelle (Météo-France, licence
ouverte 2.0, aucune clé requise) pour une station donnée — température,
humidité, pression, vent, précipitations. Pas de projection climatique
(DRIAS/RCP) ni de réanalyse en v1 — hors périmètre, RFC-0014 pour la
suite (nécessitera la clé du portail API Météo-France, AROME/DRIAS).

Une valeur SYNOP absente (champ vide dans le CSV, capteur manquant ou
paramètre non mesuré à cette station) est omise du résultat, jamais
remplacée par une valeur par défaut (ADR-009).
"""

from datetime import date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.evidence.schemas import SourceReference

# Zéro absolu — borne définitionnelle, pas un seuil météorologique.
#
# `engine.py` convertit les températures SYNOP de Kelvin en Celsius par
# soustraction de 273,15. Rien ne garantissait le sens de l'opération : une
# valeur déjà exprimée en Celsius, ou une conversion appliquée deux fois,
# produisait une température de -253 °C qui traversait le schéma sans objection
# et alimentait un diagnostic. Vérifié.
#
# **Ces bornes sont définitionnelles, jamais empiriques.** Une température
# sous le zéro absolu n'est pas improbable, elle n'existe pas ; une humidité
# relative de 250 % n'est pas un record, c'est un pourcentage de saturation
# dépassant la saturation ; un azimut de 999° n'est pas un vent violent, c'est
# un nombre hors du cercle ; une vitesse négative n'est pas une direction, une
# vitesse est une norme.
#
# La distinction est ce qui les rend admissibles au regard d'`ADR-009` :
# écrire « au-delà de 50 °C, suspect » exigerait une source climatologique et
# resterait un jugement. Écrire « sous le zéro absolu, impossible » n'en exige
# aucune — c'est la définition de l'échelle, déjà citée dans `engine.py`
# d'après le BIPM (2019), §2.3.1.
#
# Ces bornes n'attrapent donc pas une valeur douteuse. Elles attrapent une
# valeur qui n'est pas une mesure.
#
# **Limite assumee.** Le zero absolu n'attrape la double conversion que si la
# valeur d'origine etait negative : -5 °C mal converti donne -278,15 °C et
# tombe, mais 20 °C mal converti donne -253,15 °C et passe. Attraper ce cas
# supposerait une borne climatologique — le record mondial de -89,2 °C a
# Vostok, par exemple — donc empirique, exigeant sa source et relevant d'un
# arbitrage. Elle n'est pas posee ici, et la limite est ecrite plutot que tue.
_ZERO_ABSOLU_C = -273.15


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
    temperature_c: float | None = Field(default=None, ge=_ZERO_ABSOLU_C)
    humidite_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    pression_hpa: float | None = Field(default=None, gt=0.0)
    vent_direction_deg: float | None = Field(default=None, ge=0.0, le=360.0)
    vent_vitesse_ms: float | None = Field(default=None, ge=0.0)
    precipitations_1h_mm: float | None = Field(default=None, ge=0.0)
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
    officielle Météo-France, non vérifiée ici (ADR-009 : pas de sens
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
    """Un phénomène de vigilance sur un domaine (code brut Météo-France, ADR-009)."""

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
    temperature_c: float | None = Field(default=None, ge=_ZERO_ABSOLU_C)
    humidite_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    pression_hpa: float | None = Field(default=None, gt=0.0)
    vent_direction_deg: float | None = Field(default=None, ge=0.0, le=360.0)
    vent_vitesse_ms: float | None = Field(default=None, ge=0.0)
    precipitations_1h_mm: float | None = Field(default=None, ge=0.0)
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
    temperature_c: float = Field(ge=_ZERO_ABSOLU_C)
    run_modele: str = Field(description="Identifiant de couverture WCS (run de modèle utilisé)")
    resolution_deg: float = Field(default=0.01, description="Résolution native AROME France")
    source: SourceReference
