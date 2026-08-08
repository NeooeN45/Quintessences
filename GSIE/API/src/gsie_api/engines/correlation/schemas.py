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
    avec_refutation: bool = Field(
        default=False,
        description=(
            "Si vrai, exécute un test de réfutation par permutation (RFC-0015 "
            "§3.5, étape 6) en plus du calcul de corrélation. Coûteux "
            "(n_permutations recalculs) — désactivé par défaut."
        ),
    )
    n_permutations: int = Field(
        default=200,
        ge=100,
        le=5_000,
        description="Nombre de permutations pour le test de réfutation (si avec_refutation=true)",
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


class RefutationResult(BaseModel):
    """Résultat d'un test de réfutation par permutation (RFC-0015 §3.5, étape 6).

    Principe (identique au « placebo test » de DoWhy, sans la dépendance) :
    on mélange aléatoirement variable_b `n_permutations` fois — brisant
    tout lien réel entre les deux variables tout en conservant leur
    distribution marginale — et on recalcule le coefficient à chaque
    fois. Si le coefficient observé n'est pas exceptionnel par rapport à
    cette distribution de coefficients « placebo », l'association ne
    résiste pas au test le plus élémentaire de robustesse.

    Ce test ne prouve JAMAIS une causalité — il ne fait qu'écarter
    l'hypothèse que le coefficient observé soit un artefact statistique
    aussi probable qu'un mélange aléatoire (RFC-0015 §3.2, vocabulaire
    imposé : rester à « association observée », jamais « cause »).
    """

    model_config = ConfigDict(extra="forbid")

    methode: str = Field(default="permutation_placebo")
    n_permutations: int = Field(ge=100)
    p_valeur_permutation: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Proportion des coefficients placebo dont |valeur| >= |coefficient observé| — "
            "PAS la p-valeur du test de corrélation initial (voir p_valeur de CorrelationResult)"
        ),
    )
    robuste: bool = Field(
        description="p_valeur_permutation < seuil_significativite de la requête d'origine"
    )
    interpretation: str = Field(
        description=(
            "Texte imposé par RFC-0015 §3.2 — jamais le mot « cause » : "
            "« association observée, robuste au test de permutation » ou "
            "« association observée, non robuste au test de permutation »"
        )
    )


class CorrelationMatrixRequest(BaseModel):
    """Requête de calcul d'une matrice de corrélations pairwise N×N.

    Extension v1.1 — le contrat cible (CORRELATION_ENGINE.md §5) prévoit
    une liste de N paramètres. Cette extension utilise numpy.corrcoef
    (vectorisé BLAS) pour la matrice Pearson, soit 326x à 1521x plus
    rapide que scipy pairwise (benchmark BENCHMARK_CORRELATION_ENGINE.md).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(description="Identifiant de la requête")
    domaine: DomaineCorrelation = Field(description="Domaine de la corrélation")
    variables: list[ParametreCorrelation] = Field(
        min_length=2,
        max_length=200,
        description="Liste des variables à corréler (minimum 2, maximum 200)",
    )
    methode: CorrelationMethod = Field(
        default=CorrelationMethod.pearson,
        description="pearson (vectorisé numpy), spearman/kendall (scipy pairwise)",
    )
    seuil_significativite: float = Field(
        default=0.05, gt=0.0, lt=1.0, description="Seuil de p-valeur pour la significativité"
    )
    source: SourceReference = Field(
        description="Source des données observées — CON-002, toute corrélation doit être sourcée"
    )
    evidence_level: EvidenceLevel = Field(description="Niveau de preuve de la source des données")
    domaine_validite: str | None = Field(
        default=None, max_length=300, description="Ex. « France atlantique, altitude < 800 m »"
    )
    seuil_force: CorrelationStrength = Field(
        default=CorrelationStrength.moderate,
        description="Force minimale pour inclure une paire dans les résultats significatifs",
    )

    @model_validator(mode="after")
    def _valeurs_appariees(self) -> "CorrelationMatrixRequest":
        if len(self.variables) < 2:
            raise ValueError("Au moins 2 variables sont requises pour une matrice pairwise")
        n_obs = len(self.variables[0].valeurs)
        for i, var in enumerate(self.variables):
            if len(var.valeurs) != n_obs:
                raise ValueError(
                    f"Toutes les variables doivent avoir le même nombre de valeurs (appariées) "
                    f"— variable {i} ({var.variable}) a {len(var.valeurs)}, attendu {n_obs}"
                )
        return self


class PairwiseCorrelation(BaseModel):
    """Une paire de variables corrélées dans une matrice N×N."""

    model_config = ConfigDict(extra="forbid")

    variable_a: str = Field(description="Nom de la variable A (avec unité si fournie)")
    variable_b: str = Field(description="Nom de la variable B (avec unité si fournie)")
    coefficient: float = Field(ge=-1.0, le=1.0)
    p_valeur: float = Field(ge=0.0, le=1.0)
    type_relation: TypeRelation
    strength: CorrelationStrength
    n_observations: int = Field(ge=3)


class CorrelationMatrixResult(BaseModel):
    """Résultat d'une matrice de corrélations pairwise N×N."""

    model_config = ConfigDict(extra="forbid")

    requete_origine: UUID
    methode: CorrelationMethod
    n_variables: int = Field(ge=2)
    n_observations: int = Field(ge=3)
    n_paires_total: int = Field(ge=1, description="N×(N-1)/2 — nombre total de paires uniques")
    n_paires_significatives: int = Field(
        ge=0, description="Paires au-dessus du seuil de force et de significativité"
    )
    matrice: list[list[float | None]] = Field(
        description=(
            "Matrice N×N symétrique. Diagonale = None (auto-corrélation triviale). "
            "matrice[i][j] = coefficient entre variables[i] et variables[j]."
        )
    )
    variables: list[str] = Field(description="Noms des variables (avec unité si fournie)")
    paires_significatives: list[PairwiseCorrelation] = Field(
        default_factory=list,
        description="Paires triées par |coefficient| décroissant, filtrées par seuil_force",
    )
    domaine_validite: str | None = None
    source: SourceReference
    evidence_level: EvidenceLevel
    date_calcul: datetime = Field(default_factory=lambda: datetime.now(UTC))


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
    refutation: RefutationResult | None = Field(
        default=None, description="Présent uniquement si avec_refutation=true dans la requête"
    )
