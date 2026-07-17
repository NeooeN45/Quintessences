"""Schémas Pydantic pour le Botanical Engine.

Conforme à BOTANICAL_ENGINE.md §5 (contrat d'interface), avec un
périmètre v1 restreint à la taxonomie et à la nomenclature (GBIF
Backbone Taxonomy, aucune clé requise) — pas d'autécologie en v1 :
ces données (optimum pH, tolérance gel, etc.) exigent des connaissances
sourcées (Rameau et al.) pas encore ingérées dans le Knowledge Engine
(voir RFC-0014 §3.2). Un `EspeceData` v1 a donc `autecologie=None`
plutôt qu'une valeur inventée (ADR-007).
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

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
