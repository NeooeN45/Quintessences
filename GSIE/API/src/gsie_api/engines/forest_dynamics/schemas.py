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


# ─────────────────────────────────────────────────────────────────────────
# RFC-0016 — Schéma forestier spécialisé, tranche 1/10 (SiteIndexModel,
# FertilityClass). Voir gsie_api.infrastructure.models.forestry pour la
# persistance (satellite tables du métamodèle v6.2).
# ─────────────────────────────────────────────────────────────────────────


class SiteIndexModelCreate(BaseModel):
    """Modèle de fertilité (équation/table) pour une essence.

    RFC-0016 §4 : porte la méthode, l'âge de référence, sa convention et
    la région de calibration — sans ces champs, une classe de fertilité
    n'est pas comparable entre deux guides (exemple documenté : mémento
    ONF pin d'Alep, classe 1 = hauteur dominante > 14 m à 50 ans, une
    convention parmi d'autres).
    """

    model_config = ConfigDict(extra="forbid")

    species_gbif_taxon_key: int = Field(
        description="Clé GBIF du taxon accepté (usageKey) — résolu en entity_id par l'engine"
    )
    name: str = Field(min_length=1, max_length=300)
    method: str = Field(min_length=1, max_length=200, description="Ex. « table_de_production »")
    reference_age_years: int = Field(gt=0)
    age_convention: str = Field(
        min_length=1, max_length=200, description="Ex. « âge réel », « âge à 1,30 m »"
    )
    calibration_region: str = Field(min_length=1, max_length=200)
    valid_age_min_years: int | None = Field(default=None, ge=0)
    valid_age_max_years: int | None = Field(default=None, ge=0)
    source: SourceReference

    def model_post_init(self, __context: object) -> None:
        if (
            self.valid_age_min_years is not None
            and self.valid_age_max_years is not None
            and self.valid_age_min_years > self.valid_age_max_years
        ):
            raise ValueError("valid_age_min_years doit être <= valid_age_max_years")


class SiteIndexModelRecord(SiteIndexModelCreate):
    """`SiteIndexModelCreate` persisté — identifiants réels et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    species_entity_id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )


class FertilityClassCreate(BaseModel):
    """Classe de fertilité contextualisée — jamais un entier nu.

    Règle non négociable (RFC-0016 §3.1) : `species_gbif_taxon_key`,
    `site_index_model_id`, `reference_age_years`, `calibration_region` et
    `source` sont tous obligatoires. Pydantic les impose déjà via leur
    absence de valeur par défaut — un appelant ne peut pas construire
    cet objet sans les fournir tous, contrairement à un entier nu stocké
    isolément.
    """

    model_config = ConfigDict(extra="forbid")

    species_gbif_taxon_key: int = Field(
        description="Clé GBIF du taxon accepté (usageKey) — résolu en entity_id par l'engine"
    )
    site_index_model_id: UUID = Field(
        description="Référence au SiteIndexModel dont cette classe dépend — jamais nu"
    )
    class_label: str = Field(
        min_length=1, max_length=100, description="Ex. « Classe 1 », « I » — jamais un entier seul"
    )
    dominant_height_m: float | None = Field(default=None, gt=0)
    reference_age_years: int = Field(gt=0)
    lower_bound_m: float | None = Field(default=None, gt=0)
    upper_bound_m: float | None = Field(default=None, gt=0)
    calibration_region: str = Field(min_length=1, max_length=200)
    source: SourceReference

    def model_post_init(self, __context: object) -> None:
        if (
            self.lower_bound_m is not None
            and self.upper_bound_m is not None
            and self.lower_bound_m > self.upper_bound_m
        ):
            raise ValueError("lower_bound_m doit être <= upper_bound_m")


class FertilityClassRecord(FertilityClassCreate):
    """`FertilityClassCreate` persistée — identifiants réels et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    species_entity_id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )
