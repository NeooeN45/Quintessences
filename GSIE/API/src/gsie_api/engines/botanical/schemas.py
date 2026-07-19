"""Schémas Pydantic pour le Botanical Engine.

Conforme à BOTANICAL_ENGINE.md §5 (contrat d'interface), avec un
périmètre v1 restreint à la taxonomie et à la nomenclature (GBIF
Backbone Taxonomy, aucune clé requise). Un `EspeceData` v1 a donc
`autecologie=None` plutôt qu'une valeur inventée (ADR-007).

Depuis RFC-0016 (tranche 1/10), le schéma `AutecologyProfileCreate` ci-
dessous permet de modéliser une observation autécologique réelle et
sourcée (une variable à la fois) — mais reste vide tant qu'aucune
donnée réelle n'est ingérée depuis une source vérifiée (Rameau et al.,
CNPF, etc., voir RFC-0014 §3.2) : ce schéma fournit la structure, pas
son contenu.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gsie_api.engines.evidence.schemas import SourceReference


class BotanicalQueryType(StrEnum):
    """Type de requête (BOTANICAL_ENGINE.md §5) — v1 : par_essence/par_taxon uniquement."""

    par_essence = "par_essence"
    par_taxon = "par_taxon"


class TaxonStatus(StrEnum):
    """Statut taxonomique GBIF."""

    accepted = "ACCEPTED"
    synonym = "SYNONYM"
    doubtful = "DOUBTFUL"


class BotanicalQuery(BaseModel):
    """Requête d'identification taxonomique (GBIF Backbone Taxonomy)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    type: BotanicalQueryType = BotanicalQueryType.par_essence
    essence: str = Field(
        min_length=1, max_length=200, description="Nom scientifique (ex. Quercus petraea)"
    )


class EspeceData(BaseModel):
    """Données d'une espèce (BOTANICAL_ENGINE.md §5) — v1 : taxonomie/nomenclature uniquement."""

    model_config = ConfigDict(extra="forbid")

    taxon_id: UUID = Field(description="UUID de la resource `entity` persistée")
    gbif_taxon_key: int = Field(description="Clé GBIF du taxon accepté (usageKey)")
    nom_scientifique: str
    nom_vernaculaire: str | None = None
    synonymes: list[str] = Field(default_factory=list, max_length=50)
    famille: str | None = None
    statut: TaxonStatus
    taxonomie_version: str = Field(default="GBIF Backbone Taxonomy")
    autecologie: None = Field(
        default=None,
        description="Hors périmètre v1 — nécessite des connaissances sourcées non encore ingérées",
    )
    source: SourceReference


class BotanicalData(BaseModel):
    """Résultat d'une requête botanique (BOTANICAL_ENGINE.md §5)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    especes: list[EspeceData] = Field(default_factory=list, max_length=50)
    source: SourceReference
    date_donnees: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StatutIndigenatFrance(StrEnum):
    """Statut d'indigénat à l'échelle de la France hexagonale + Corse (Bellifa et al. 2026)."""

    exogene_archeophyte = "0 - A"
    exogene_neophyte = "0 - N"
    indigene = "1"
    cryptogene = "9"


class StatutIndigenatRegion(StrEnum):
    """Statut d'indigénat à l'échelle de la sylvoécorégion (SER) — Bellifa et al. 2026."""

    exogene_ou_absent = "0"
    indigene = "1"
    probablement_indigene = "2"
    probablement_exogene = "3"
    exogene = "9"


class IndigenatQuery(BaseModel):
    """Requête de statut d'indigénat d'une essence pour une sylvoécorégion (SER) donnée.

    Une des deux identifications du taxon est requise : `cd_nom` (exact,
    référentiel TAXREFv18.0) ou `nom_scientifique` (recherche exacte,
    sensible aux variantes de nomenclature — préférer cd_nom si connu).
    """

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    cd_nom: int | None = Field(default=None, description="Identifiant CD_NOM TAXREFv18.0")
    nom_scientifique: str | None = Field(
        default=None, min_length=1, max_length=200, description="Ex. « Quercus petraea »"
    )
    code_ser: str = Field(
        min_length=2, max_length=3, description="Code de sylvoécorégion, ex. « A11 »"
    )

    @model_validator(mode="after")
    def _identifiant_requis(self) -> "IndigenatQuery":
        if self.cd_nom is None and not self.nom_scientifique:
            raise ValueError("cd_nom ou nom_scientifique requis")
        return self


class IndigenatResult(BaseModel):
    """Statut d'indigénat réel d'une essence pour une sylvoécorégion donnée."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    nom_scientifique: str
    nom_vernaculaire: str | None = None
    cd_nom: int | None = None
    famille: str | None = None
    statut_france: StatutIndigenatFrance
    code_ser: str
    statut_ser: StatutIndigenatRegion
    source: SourceReference


class TaxrefQuery(BaseModel):
    """Requête de résolution TAXREF (référentiel taxonomique canonique — SCI-003)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    nom_scientifique: str = Field(min_length=1, max_length=200)


class TaxrefResult(BaseModel):
    """Entrée TAXREF réelle résolue (cd_nom = `taxonID` du miroir GBIF)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    cd_nom: int = Field(description="Identifiant CD_NOM TAXREF (champ taxonID du miroir GBIF)")
    nom_scientifique: str
    nom_scientifique_complet: str = Field(description="Avec auteur et année (scientificName)")
    nom_vernaculaire: str | None = None
    famille: str | None = None
    statut: TaxonStatus
    taxonomie_version: str = Field(default="TAXREF (miroir GBIF)")
    source: SourceReference


# ─────────────────────────────────────────────────────────────────────────
# RFC-0016 — Schéma forestier spécialisé, tranche 1/10 (AutecologyProfile).
# Lève partiellement la restriction documentée en tête de ce module :
# l'autécologie devient modélisable (une variable sourcée à la fois),
# mais reste vide tant qu'aucune valeur réelle n'est ingérée (ADR-007 —
# ce schéma ne fournit aucune valeur par défaut inventée).
# ─────────────────────────────────────────────────────────────────────────


class AutecologyProfileCreate(BaseModel):
    """Une observation autécologique sourcée pour un taxon — une variable à la fois.

    RFC-0016 §4 : jamais une « note globale » par essence. Chaque valeur
    (pH optimal, tolérance sécheresse, etc.) est sa propre ligne, avec sa
    propre source et sa propre incertitude — `value_numeric` et
    `value_text` sont mutuellement facultatifs mais au moins l'un des
    deux est requis (imposé par `model_post_init`, reflète la contrainte
    SQL `ck_autecology_profile_value_present`).
    """

    model_config = ConfigDict(extra="forbid")

    species_gbif_taxon_key: int = Field(
        description="Clé GBIF du taxon accepté (usageKey) — résolu en entity_id par l'engine"
    )
    variable: str = Field(
        min_length=1, max_length=200, description="Ex. « ph_optimal », « tolerance_secheresse »"
    )
    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=2000)
    unit: str | None = Field(default=None, max_length=50)
    life_stage: str | None = Field(
        default=None, max_length=100, description="Ex. « adulte », « semis »"
    )
    season: str | None = Field(default=None, max_length=50)
    territory_description: str | None = Field(default=None, max_length=2000)
    method: str | None = None
    uncertainty: str | None = None
    evidence_level: str = Field(
        description="Grade A-F, voir gsie_api.infrastructure.models.enums.EvidenceLevel"
    )
    source: SourceReference

    def model_post_init(self, __context: object) -> None:
        if self.value_numeric is None and self.value_text is None:
            raise ValueError("value_numeric ou value_text requis (au moins l'un des deux)")


class AutecologyProfileRecord(AutecologyProfileCreate):
    """`AutecologyProfileCreate` persistée — identifiants réels et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    species_entity_id: UUID
    status: str = Field(
        description="draft | proposed | accepted | superseded | rejected | deprecated"
    )
