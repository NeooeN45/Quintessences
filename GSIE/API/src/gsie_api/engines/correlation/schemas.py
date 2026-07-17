"""Schémas Pydantic pour le Correlation Engine.

Conforme à CORRELATION_ENGINE.md §5 (contrat d'interface), avec une
réduction de périmètre v1 assumée et documentée : le contrat original
prévoit que les valeurs numériques soient récupérées auprès des moteurs
domaine (GIS, Climate, Pedology, Botanical, Forest Dynamics) via
`ParametreCorrelation.source_moteur`. Ces moteurs n'existent pas encore
(seul GIS a un placeholder). En v1, les valeurs sont donc fournies
directement dans la requête (`ParametreCorrelation.valeurs`) — le champ
`source_moteur` reste renseigné pour la provenance/traçabilité et pour
permettre un branchement futur sans revoir le contrat.

De même, le contrat original permet une liste de N paramètres (matrice
de corrélations pairwise). En v1, une seule paire (variable_a,
variable_b) est calculée par requête — plus simple à vérifier et à
faire évoluer vers un vrai N×N plus tard sans rupture de contrat.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference
from gsie_api.infrastructure.models.enums import CorrelationMethod, CorrelationStrength


class SourceMoteur(StrEnum):
    """Moteur domaine d'origine de la variable (CORRELATION_ENGINE.md §5)."""

    gis = "GIS"
    climate = "CLIMATE"
    pedology = "PEDOLOGY"
    botanical = "BOTANICAL"
    forest_dynamics = "FOREST_DYNAMICS"
    terrain = "TERRAIN"


class DomaineCorrelation(StrEnum):
    """Domaine de la requête de corrélation (CORRELATION_ENGINE.md §5)."""

    stationnel = "stationnel"
    climatique = "climatique"
    sylvicole = "sylvicole"
    sanitaire = "sanitaire"
    global_ = "global"


class TypeRelation(StrEnum):
    """Nature de la relation détectée (CORRELATION_ENGINE.md §5)."""

    positive = "positive"
    negative = "negative"
    non_significative = "non_significative"


class ParametreCorrelation(BaseModel):
    """Une variable à corréler, avec ses valeurs observées (extension v1)."""

    model_config = ConfigDict(extra="forbid")

    source_moteur: SourceMoteur = Field(description="Moteur domaine d'origine (provenance)")
    variable: str = Field(
        min_length=1, max_length=200, description="Ex. « pH », « precipitations_estivales »"
    )
    unite: str | None = Field(default=None, max_length=50)
    valeurs: list[float] = Field(
        min_length=3,
        max_length=100_000,
        description=(
            "Valeurs observées, appariées avec l'autre variable par position "
            "(valeurs[i] et l'autre variable valeurs[i] décrivent la même "
            "observation). Minimum 3 points — en dessous, un coefficient de "
            "corrélation n'a pas de sens statistique interprétable."
        ),
    )


class CorrelationComputeRequest(BaseModel):
    """Requête de calcul d'une corrélation entre deux variables."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(description="Identifiant de la requête")
    domaine: DomaineCorrelation = Field(description="Domaine de la corrélation")
    variable_a: ParametreCorrelation
    variable_b: ParametreCorrelation
    methode: CorrelationMethod = Field(
        default=CorrelationMethod.pearson,
        description="pearson (linéaire), spearman ou kendall (rang, robuste aux non-linéarités)",
    )
    seuil_significativite: float = Field(
        default=0.05, gt=0.0, lt=1.0, description="Seuil de p-valeur pour la significativité"
    )
    source: SourceReference = Field(
        description="Source des données observées — CON-002, toute corrélation doit être sourcée"
    )
    evidence_level: EvidenceLevel = Field(
        description=(
            "Niveau de preuve de la SOURCE des données (pas de la corrélation "
            "elle-même — un coefficient statistique ne détermine pas la "
            "crédibilité de sa source, voir docstring engine.py)"
        )
    )
    domaine_validite: str | None = Field(
        default=None, max_length=300, description="Ex. « France atlantique, altitude < 800 m »"
    )

    @model_validator(mode="after")
    def _valeurs_appariees(self) -> "CorrelationComputeRequest":
        if len(self.variable_a.valeurs) != len(self.variable_b.valeurs):
            raise ValueError(
                "variable_a et variable_b doivent avoir le même nombre de valeurs "
                f"(appariées) — reçu {len(self.variable_a.valeurs)} et "
                f"{len(self.variable_b.valeurs)}"
            )
        return self


class CorrelationResult(BaseModel):
    """Résultat d'un calcul de corrélation (CORRELATION_ENGINE.md §5 — Correlation)."""

    model_config = ConfigDict(extra="forbid")

    correlation_id: UUID = Field(description="Identifiant de la corrélation persistée")
    requete_origine: UUID
    variable_a: str = Field(description="Nom de la variable A (avec unité si fournie)")
    variable_b: str = Field(description="Nom de la variable B (avec unité si fournie)")
    methode: CorrelationMethod
    coefficient: float = Field(ge=-1.0, le=1.0)
    p_valeur: float = Field(ge=0.0, le=1.0)
    type_relation: TypeRelation
    strength: CorrelationStrength
    n_observations: int = Field(ge=3)
    domaine_validite: str | None = None
    source: SourceReference
    evidence_level: EvidenceLevel
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "1 - p_valeur (bornée [0,1]) — indicateur simple, pas une probabilité bayésienne"
        ),
    )
    date_calcul: datetime = Field(default_factory=lambda: datetime.now(UTC))
