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


# ─────────────────────────────────────────────────────────────────────────
# RFC-0016 — Schéma forestier spécialisé, tranche 2/10 (StationType,
# StationObservation) — diagnostic stationnel, étape 2 de la chaîne de
# décision professionnelle (RFC-0016 §3.3).
# ─────────────────────────────────────────────────────────────────────────


class StationTypeCreate(BaseModel):
    """Unité conceptuelle de station issue d'un guide — pas une observation terrain.

    RFC-0016 §4.3 : `StationType` décrit ce qu'un guide définit ;
    `StationObservation` décrit ce qui est réellement observé sur une
    parcelle. Ne jamais confondre les deux : un `StationType` ne peut
    pas être créé à partir d'une seule parcelle observée.
    """

    model_config = ConfigDict(extra="forbid")

    guide: str = Field(
        min_length=1, max_length=300, description="Ex. « Guide des stations Aquitaine »"
    )
    guide_version: str = Field(min_length=1, max_length=100)
    validity_zone_description: str = Field(
        min_length=1, description="Zone de validité en texte libre (pas de géométrie en tranche 2)"
    )
    ser_greco_code: str | None = Field(default=None, max_length=50)
    topography_description: str | None = None
    substrate_description: str | None = None
    hydromorphy_description: str | None = None
    indicator_flora_description: str | None = None
    source: SourceReference


class StationTypeRecord(StationTypeCreate):
    """`StationTypeCreate` persisté — identifiant réel et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )


class StationObservationCreate(BaseModel):
    """Ce qui est réellement observé sur une parcelle — jamais confondu avec `StationType`.

    RFC-0016 §4.3 : conserve le chemin suivi dans la clé du guide
    (`key_path_followed`). Si aucun `StationType` ne peut être déterminé
    avec certitude, `station_type_id` reste `None` mais
    `determination_uncertainty` devient alors obligatoire (imposé par
    `model_post_init`, reflète la contrainte SQL
    `ck_station_observation_uncertainty_when_undetermined`) — jamais un
    rattachement arbitraire pour "faire simple".
    """

    model_config = ConfigDict(extra="forbid")

    plot_reference: str = Field(min_length=1, max_length=200)
    station_type_id: UUID | None = None
    key_path_followed: str | None = Field(
        default=None, description="Réponses saisies et embranchement obtenu dans la clé du guide"
    )
    topography_observed: str | None = None
    substrate_observed: str | None = None
    hydromorphy_observed: str | None = None
    indicator_flora_observed: str | None = None
    available_water_capacity_mm: float | None = Field(default=None, ge=0)
    available_water_capacity_method: str | None = Field(default=None, max_length=300)
    determination_uncertainty: str | None = None
    observed_at: datetime
    source: SourceReference

    def model_post_init(self, __context: object) -> None:
        if self.station_type_id is None and not self.determination_uncertainty:
            raise ValueError(
                "determination_uncertainty requis lorsque station_type_id est absent "
                "(aucune StationType déterminée avec certitude)"
            )


class StationObservationRecord(StationObservationCreate):
    """`StationObservationCreate` persistée — identifiant réel et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )


# ─────────────────────────────────────────────────────────────────────────
# RFC-0016 — Schéma forestier spécialisé, tranche 3/10 (SilviculturalSystem,
# SilviculturalRule) — itinéraires sylvicoles (RFC-0016 §3.1). `Intervention`
# (troisième entité citée par le RFC) n'a pas de schéma dédié ici : elle
# existe déjà (gsie_api.engines côté business, type resource `intervention`,
# audit ONF/CNPF 2026-07-16) et couvre le même besoin.
# ─────────────────────────────────────────────────────────────────────────


class SilviculturalSystemCreate(BaseModel):
    """Système sylvicole — futaie régulière/irrégulière, taillis, conversion."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=300)
    category: str = Field(
        description="futaie_reguliere | futaie_irreguliere | taillis | "
        "taillis_sous_futaie | conversion | autre"
    )
    description: str | None = None
    source: SourceReference


class SilviculturalSystemRecord(SilviculturalSystemCreate):
    """`SilviculturalSystemCreate` persisté — identifiant réel et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )


class SilviculturalRuleCreate(BaseModel):
    """Règle d'intervention sylvicole — contexte, déclencheur, action, preuve.

    RFC-0016 §3.1 : `required_context`, `trigger`, `action`, `intensity`,
    `evidence_level` et `source` sont tous obligatoires — une règle sans
    ces champs ne serait pas actionnable ni traçable jusqu'à sa preuve.
    """

    model_config = ConfigDict(extra="forbid")

    silvicultural_system_id: UUID | None = None
    species_gbif_taxon_key: int | None = Field(
        default=None,
        description="Clé GBIF du taxon accepté, si la règle est spécifique à une essence",
    )
    required_context: str = Field(
        min_length=1, description="Contexte requis pour appliquer la règle"
    )
    trigger: str = Field(
        min_length=1, description="Déclencheur (ex. seuil de densité, âge, sanitaire)"
    )
    action: str = Field(min_length=1, description="Action recommandée (ex. éclaircie, coupe rase)")
    intensity: str = Field(
        min_length=1, description="Intensité de l'action, qualitative ou chiffrée"
    )
    evidence_level: str = Field(description="A | B | C | D | E | F")
    source: SourceReference


class SilviculturalRuleRecord(SilviculturalRuleCreate):
    """`SilviculturalRuleCreate` persistée — identifiant réel, statut et validation humaine.

    RFC-0016 §3.2 : le passage à `accepted` (équivalent du `APPROVED` du
    corpus source) exige `human_validator` non nul — jamais une
    auto-validation par le pipeline d'extraction.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID
    species_entity_id: UUID | None = None
    human_validator: str | None = Field(
        default=None, max_length=300, description="Nom/qualité du validateur humain"
    )
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )

    def model_post_init(self, __context: object) -> None:
        if self.status == "accepted" and not self.human_validator:
            raise ValueError(
                "human_validator requis lorsque status='accepted' "
                "(jamais d'auto-validation par le pipeline d'extraction)"
            )


# ─────────────────────────────────────────────────────────────────────────
# RFC-0016 — Schéma forestier spécialisé, tranche 4/10 (ProvenanceMaterial)
# — provenance / matériel forestier de reproduction (MFR) pour une
# proposition de plantation (RFC-0016 §3.1).
# ─────────────────────────────────────────────────────────────────────────


class ProvenanceMaterialCreate(BaseModel):
    """Provenance / MFR pour une proposition de plantation — jamais une essence nue.

    RFC-0016 §3.1 : `species_gbif_taxon_key`, `provenance_region`,
    `base_material_category`, `aid_eligible`, `decree_version` et
    `source` sont tous obligatoires — une proposition de plantation qui
    cite un matériel « admissible aux aides » sans la version de
    l'arrêté qui le rend admissible est le même bug de sécurité
    scientifique qu'une classe de fertilité sans région de calibration.
    """

    model_config = ConfigDict(extra="forbid")

    species_gbif_taxon_key: int = Field(
        description="Clé GBIF du taxon accepté (usageKey) — résolu en entity_id par l'engine"
    )
    provenance_region: str = Field(min_length=1, max_length=200)
    base_material: str = Field(
        min_length=1,
        max_length=300,
        description="Identifiant du matériel de base (verger à graines, peuplement classé, etc.)",
    )
    base_material_category: str = Field(description="identifie | selectionne | qualifie | teste")
    aid_eligible: bool = Field(description="Admissibilité aux aides publiques, selon l'arrêté cité")
    decree_version: str = Field(
        min_length=1,
        max_length=300,
        description="Version de l'arrêté MFR (ex. « arrêté du 6 mars 2026 »)",
    )
    valid_region_description: str | None = None
    source: SourceReference


class ProvenanceMaterialRecord(ProvenanceMaterialCreate):
    """`ProvenanceMaterialCreate` persisté — identifiants réels et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    species_entity_id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )


# ─────────────────────────────────────────────────────────────────────────
# RFC-0016 — Schéma forestier spécialisé, tranche 5/10 (DiagnosticProtocol,
# HealthRisk) — protocoles sanitaires (ARCHI, DEPERIS, IBP, RFC-0016 §3.1).
# ─────────────────────────────────────────────────────────────────────────


class DiagnosticProtocolCreate(BaseModel):
    """Protocole sanitaire documenté (ARCHI, DEPERIS, IBP, etc.)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    criteria_description: str = Field(min_length=1)
    thresholds_description: str = Field(min_length=1)
    limitations: str | None = None
    source: SourceReference


class DiagnosticProtocolRecord(DiagnosticProtocolCreate):
    """`DiagnosticProtocolCreate` persisté — identifiant réel et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )


class HealthRiskCreate(BaseModel):
    """Diagnostic sanitaire sur un sujet — jamais une certitude sans méthode.

    RFC-0016 §3.1 : `symptom_observed` est toujours obligatoire (ce qui a
    réellement été vu). `confirmed_causal_agent` exige
    `confirmation_method` — un agent « confirmé » sans méthode de
    confirmation citée serait une invention silencieuse (ADR-007).
    """

    model_config = ConfigDict(extra="forbid")

    subject_id: UUID
    diagnostic_protocol_id: UUID | None = None
    symptom_observed: str = Field(min_length=1)
    suspected_causal_agent: str | None = Field(default=None, max_length=300)
    confirmed_causal_agent: str | None = Field(default=None, max_length=300)
    confirmation_method: str | None = None
    severity: str | None = Field(
        default=None, description="negligible | low | moderate | high | critical"
    )
    observed_at: datetime
    source: SourceReference

    def model_post_init(self, __context: object) -> None:
        if self.confirmed_causal_agent and not self.confirmation_method:
            raise ValueError(
                "confirmation_method requis lorsque confirmed_causal_agent est renseigné "
                "(un agent confirmé sans méthode citée serait une invention silencieuse)"
            )


class HealthRiskRecord(HealthRiskCreate):
    """`HealthRiskCreate` persisté — identifiant réel et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )
