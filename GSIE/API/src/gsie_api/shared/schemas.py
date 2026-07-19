"""Schemas Pydantic communs — pagination, erreurs, réponses standard.

RFC-0016 §3.4 (Phase B, point 6) : `DecisionPassportCategory` et
`DecisionPassportItem` implémentent le passeport de décision — chaque
élément d'un diagnostic ou d'un scénario forestier doit être classé
dans une et une seule des cinq catégories, avec sa propre justification
non négociable (jamais une recommandation présentée comme une
certitude). Généralise le principe déjà posé pour AROME (RFC-0015
§3.2 : observation/estimation/simulation/recommandation) au domaine
sylvicole — cross-engine, donc placé ici plutôt que dans un engine
particulier.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PageParams(BaseModel):
    """Paramètres de pagination (global_rules — pas de listes non bornées)."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(max_length=1000)
    error_code: str | None = Field(default=None, max_length=50)
    trace_id: str | None = Field(default=None, max_length=64)


class HealthResponse(BaseModel):
    """Réponse des endpoints health/ready."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="healthy|degraded|unhealthy")
    version: str
    environment: str
    timestamp: datetime
    dependencies: dict[str, str] = Field(
        default_factory=dict,
        description="État des dépendances (database, redis)",
    )


class EngineStatusResponse(BaseModel):
    """Réponse standardisée pour le statut d'un moteur."""

    model_config = ConfigDict(extra="forbid")

    engine: str = Field(description="Nom du moteur")
    status: str = Field(description="not_implemented|active|degraded")
    planned_week: int = Field(description="Semaine d'implémentation prévue")
    language: str = Field(description="Langage d'implémentation")


class EngineVersionResponse(BaseModel):
    """Réponse standardisée pour la version d'un moteur."""

    model_config = ConfigDict(extra="forbid")

    version: str
    backend: str


class DecisionPassportCategory(StrEnum):
    """Les cinq catégories du passeport de décision (RFC-0016 §3.4).

    Jamais fusionnables : un élément « modélisé » présenté sans cette
    étiquette se lirait comme une mesure, exactement le risque que
    cette RFC nomme (§2.2 : « la recommandation ne doit pas être
    "l'IA recommande le Douglas", mais une chaîne traçable »).
    """

    observe = "observe"
    calcule = "calcule"
    modelise = "modelise"
    documente_recommande = "documente_recommande"
    incertain = "incertain"


class DecisionPassportItem(BaseModel):
    """Un élément d'un diagnostic ou d'un scénario, classé et justifié.

    Chaque catégorie impose sa propre justification non négociable,
    imposée par `model_post_init` — jamais une valeur affichée sans la
    preuve qui la classe :

    - `observe` : `protocol_or_method` obligatoire (comment la mesure a
      été prise) ;
    - `calcule` : `method` obligatoire (formule déterministe utilisée) ;
    - `modelise` : `model_reference` obligatoire (le modèle qui a
      produit la sortie, ex. un `SiteIndexModel`) ;
    - `documente_recommande` : `source_page_or_table` obligatoire
      (localisation précise dans la source citée, même règle que
      `EvidenceStatement`, RFC-0016 tranche 6/10) ;
    - `incertain` : `uncertainty_reason` obligatoire (désaccord entre
      sources ou donnée manquante — jamais un silence).
    """

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=300)
    value: str = Field(min_length=1, description="Valeur ou conclusion affichée")
    category: DecisionPassportCategory
    protocol_or_method: str | None = None
    method: str | None = None
    model_reference: UUID | None = Field(
        default=None, description="Référence au modèle (ex. SiteIndexModel.id)"
    )
    source_page_or_table: str | None = Field(default=None, max_length=200)
    uncertainty_reason: str | None = None

    def model_post_init(self, __context: object) -> None:
        required_by_category = {
            DecisionPassportCategory.observe: ("protocol_or_method", self.protocol_or_method),
            DecisionPassportCategory.calcule: ("method", self.method),
            DecisionPassportCategory.modelise: ("model_reference", self.model_reference),
            DecisionPassportCategory.documente_recommande: (
                "source_page_or_table",
                self.source_page_or_table,
            ),
            DecisionPassportCategory.incertain: ("uncertainty_reason", self.uncertainty_reason),
        }
        field_name, field_value = required_by_category[self.category]
        if not field_value:
            raise ValueError(
                f"{field_name} requis lorsque category='{self.category}' "
                "(chaque catégorie du passeport de décision porte sa propre "
                "justification non négociable, RFC-0016 §3.4)"
            )


class DecisionPassport(BaseModel):
    """Passeport de décision complet — un diagnostic ou un scénario forestier.

    RFC-0016 §3.4 : exposé par l'API pour que l'utilisateur distingue
    toujours visuellement ce qui a été mesuré de ce qui a été modélisé,
    recommandé ou reste incertain.
    """

    model_config = ConfigDict(extra="forbid")

    subject_id: UUID = Field(description="Peuplement, parcelle ou entité diagnostiquée")
    items: list[DecisionPassportItem] = Field(min_length=1, max_length=200)
    generated_at: datetime
