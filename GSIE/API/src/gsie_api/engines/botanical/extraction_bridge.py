"""Pont entre l'extraction documentaire (RFC-0014 §3.2) et `AutecologyProfile`.

RFC-0016 §5, Phase B, point 4.

Le pipeline d'extraction (`Forge/src/dataset_forge/documents/extraction.py`,
`KnowledgeExtractor`) produit des faits atomiques en statut `quarantine`
— une citation exacte vérifiée mot pour mot dans le texte source, mais
jamais validée automatiquement (voir RFC-0014 §3.6, troisième pilote :
29 faits vérifiés sur *Quercus robur*/*Q. petraea*,
`GSIE/KNOWLEDGE/pilotes_extraction/parelle_2007_quercus_waterlogging_facts.json`).

Ce module ne fait PAS le pont automatiquement — un fait en langage
naturel (« Quercus petraea se trouve sur des sols acides profonds et
bien drainés ») ne peut pas être transformé en `variable`/`value_numeric`/
`value_text` structurés par une heuristique : ce serait exactement le
risque nommé par RFC-0016 (« jamais par heuristique »). Le curateur
humain doit donc fournir explicitement `variable`, `evidence_level` et
la valeur — cette fonction se contente de :

1. refuser tout fait qui n'est pas en statut `quarantine` (un fait déjà
   `rejete` par la vérification de citation ne doit jamais être
   ingéré, quelle que soit la décision du curateur) ;
2. construire automatiquement le champ `method` à partir de la
   citation exacte et de la page — pour que la traçabilité jusqu'à
   l'extrait vérifié soit garantie par construction, pas retapée à la
   main (source d'erreur de transcription).
"""

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.botanical.schemas import AutecologyProfileCreate
from gsie_api.engines.evidence.schemas import SourceReference


class QuarantinedFact(BaseModel):
    """Un fait atomique extrait par `KnowledgeExtractor`, tel que persisté en JSON.

    Miroir du schéma produit par
    `Forge/src/dataset_forge/documents/extraction.py` — voir RFC-0014
    §3.6 (pilotes réalisés) pour le format exact.
    """

    model_config = ConfigDict(extra="forbid")

    document_title: str = Field(min_length=1)
    document_reference: str = Field(min_length=1, max_length=500)
    page_number: int = Field(gt=0)
    fait: str = Field(min_length=1, description="Fait en langage naturel, jamais utilisé tel quel")
    citation_extrait: str = Field(min_length=1, description="Citation vérifiée mot pour mot")
    confiance_llm: float = Field(ge=0.0, le=1.0)
    statut: str = Field(description="quarantine | rejete | accepte")
    rejet_raison: str | None = None


class ExtractionBridgeError(Exception):
    """Erreur de base du pont extraction → AutecologyProfile."""


def build_autecology_profile_from_quarantined_fact(
    fact: QuarantinedFact,
    *,
    species_gbif_taxon_key: int,
    variable: str,
    evidence_level: str,
    source: SourceReference,
    value_numeric: float | None = None,
    value_text: str | None = None,
    unit: str | None = None,
    life_stage: str | None = None,
    season: str | None = None,
    territory_description: str | None = None,
    uncertainty: str | None = None,
) -> AutecologyProfileCreate:
    """Construit un `AutecologyProfileCreate` à partir d'un fait en quarantaine validé.

    `variable`, `evidence_level`, `source` et la valeur
    (`value_numeric`/`value_text`) restent des décisions du curateur
    humain — jamais dérivées automatiquement du texte de `fact.fait`
    (voir docstring module). Seul le champ `method` est construit
    automatiquement, à partir de la citation déjà vérifiée par
    `KnowledgeExtractor`.

    Lève `ExtractionBridgeError` si `fact.statut != "quarantine"` — un
    fait déjà rejeté (citation introuvable) ne doit jamais devenir une
    `AutecologyProfile`, quelle que soit la décision du curateur.
    """
    if fact.statut != "quarantine":
        raise ExtractionBridgeError(
            f"Fait en statut '{fact.statut}' (attendu 'quarantine') — "
            "un fait rejeté par la vérification de citation ne peut pas devenir "
            "une AutecologyProfile"
        )

    method = (
        f"Extraction documentaire sourcée (RFC-0014 §3.2) — {fact.document_reference}, "
        f"p. {fact.page_number} : « {fact.citation_extrait} »"
    )

    return AutecologyProfileCreate(
        species_gbif_taxon_key=species_gbif_taxon_key,
        variable=variable,
        value_numeric=value_numeric,
        value_text=value_text,
        unit=unit,
        life_stage=life_stage,
        season=season,
        territory_description=territory_description,
        method=method,
        uncertainty=uncertainty,
        evidence_level=evidence_level,
        source=source,
    )
