"""Schémas Pydantic pour le Forest Dynamics Engine.

Conforme à FOREST_DYNAMICS_ENGINE.md §5 (contrat d'interface complet).

Périmètre v1 (voir docstring engine.py) : calcul dendrométrique
géométrique réel (surface terrière, volume approché) à partir d'un
`PeuplementState` mesuré — pas de projection de croissance
(`TrajectoireCroissance`) en v1. Un vrai modèle de croissance (ONF-FFN,
CAPSIS) exige des coefficients publiés que nous n'avons pas encore
sourcés et vérifiés, ou une calibration IFN réelle (RFC-0013, données
bulk non encore ingérées) — les inventer violerait la garantie du
moteur (§6 : « aucun coefficient n'est inventé ») et ADR-007.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.evidence.schemas import SourceReference


class StructurePeuplement(StrEnum):
    """Structure du peuplement (FOREST_DYNAMICS_ENGINE.md §5)."""

    reguliere = "reguliere"
    irreguliere = "irreguliere"
    melange = "melange"
    taillis = "taillis"


class PeuplementState(BaseModel):
    """État mesuré d'un peuplement (FOREST_DYNAMICS_ENGINE.md §5)."""

    model_config = ConfigDict(extra="forbid")

    essence_principale: str = Field(min_length=1, max_length=200)
    age_moyen: float = Field(ge=0, description="Années")
    densite_t_ha: float = Field(gt=0, description="Tiges par hectare")
    diametre_moyen_cm: float = Field(gt=0, description="Diamètre moyen (cm)")
    hauteur_moyenne_m: float = Field(gt=0, description="Hauteur moyenne (m)")
    structure: StructurePeuplement = StructurePeuplement.reguliere
    source_inventaire: SourceReference


class DendrometricRequest(BaseModel):
    """Requête de calcul dendrométrique géométrique à partir d'un état mesuré.

    Périmètre v1 du contrat `DynamicsRequest` — sans horizon de
    projection ni perturbations (pas de modèle de croissance en v1).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    peuplement_id: UUID = Field(default_factory=uuid4)
    etat_initial: PeuplementState


class CaracteristiqueDendrometrique(BaseModel):
    """Une caractéristique dendrométrique calculée géométriquement."""

    model_config = ConfigDict(extra="forbid")

    nom: str = Field(description="Ex. « surface_terriere », « volume_approche »")
    valeur: float
    unite: str
    methode: str = Field(description="Formule géométrique utilisée, citée")


class DendrometricResult(BaseModel):
    """Résultat d'un calcul dendrométrique (sous-ensemble de DynamicsProjection).

    v1 : caractéristiques géométriques uniquement — pas de
    `trajectoires` (projection de croissance), voir docstring module.
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    peuplement_id: UUID
    caracteristiques: list[CaracteristiqueDendrometrique] = Field(
        default_factory=list, max_length=20
    )
    source: SourceReference
    date_calcul: datetime = Field(default_factory=lambda: datetime.now(UTC))
