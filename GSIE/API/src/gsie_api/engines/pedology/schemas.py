"""Schémas Pydantic pour le Pedology Engine.

Conforme à PEDOLOGY_ENGINE.md §5 (contrat d'interface), avec un
périmètre v1 restreint aux propriétés de sol modélisées par SoilGrids
(ISRIC, aucune clé requise) pour un point donné : pH (H2O), argile,
sable, limon (0-5cm). Pas de `ProfilSol` (horizons détaillés) ni de
`ClassificationSol` (RPF/WRB) en v1 — ces données exigent le
Référentiel Pédologique Forestier (RFC-0013, sous accord ONF/INRAE non
encore formalisé), pas une valeur approximée (ADR-007).

Niveau de preuve (EVIDENCE_FRAMEWORK.md §4.2, cas Pédologie) : SoilGrids
est un produit peer-reviewed unique (Poggio et al., 2021, SOIL
journal) — plafond **B** (établi) en l'absence de convergence
multi-sources, jamais A.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference


class PedologyQuery(BaseModel):
    """Requête de propriétés de sol pour un point (SoilGrids ISRIC)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    latitude: float = Field(ge=-90.0, le=90.0, description="WGS 84")
    longitude: float = Field(ge=-180.0, le=180.0, description="WGS 84")
    profondeur: str = Field(
        default="0-5cm",
        description="Tranche de profondeur SoilGrids (ex. 0-5cm, 5-15cm, 15-30cm)",
    )


class SolCaracteristique(BaseModel):
    """Une caractéristique de sol (PEDOLOGY_ENGINE.md §5)."""

    model_config = ConfigDict(extra="forbid")

    nom: str = Field(description="Ex. « ph », « argile_pct », « sable_pct »")
    valeur: float
    unite: str
    source: SourceReference
    evidence_level: EvidenceLevel = EvidenceLevel.B


class PedologyData(BaseModel):
    """Résultat d'une requête pédologique (PEDOLOGY_ENGINE.md §5).

    v1 : sans profil de sol ni classification (voir docstring module).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    latitude: float
    longitude: float
    profondeur: str
    caracteristiques: list[SolCaracteristique] = Field(default_factory=list, max_length=20)
    source: SourceReference
    date_donnees: datetime = Field(default_factory=lambda: datetime.now(UTC))
