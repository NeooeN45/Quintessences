"""Schémas Pydantic pour le Knowledge Engine.

Conforme à KNOWLEDGE_ENGINE.md §5 (contrat d'interface) et
KNOWLEDGE_METHOD.md §2 (structure d'un KnowledgeObject) :
- KnowledgeObject (nœud de connaissance versionné)
- KnowledgeQuery (requête sur le graphe)
- KnowledgeQueryResult (réponse de requête)
- VersionEntry (historique de version — CON-010)
- DomaineValidite (conditions d'application)
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.evidence.schemas import (
    ConflitBibliographique,
    EvidenceLevel,
    KnowledgeStatus,
    SourceReference,
)


class KnowledgeType(StrEnum):
    """Type de KnowledgeObject (KNOWLEDGE_METHOD.md §2, livrable 302)."""
    concept = "concept"
    relation = "relation"
    regle = "regle"
    seuil = "seuil"
    modele = "modele"
    classification = "classification"


class QueryType(StrEnum):
    """Type de requête sur le graphe (KNOWLEDGE_ENGINE.md §5)."""
    par_concept = "par_concept"
    par_relation = "par_relation"
    par_domaine = "par_domaine"
    par_essence = "par_essence"
    par_station = "par_station"


class DomaineScientifique(StrEnum):
    """Domaine scientifique (Constitution Scientifique S-6)."""
    ecologie_forestiere = "ecologie_forestiere_et_stationnelle"
    pedologie = "pedologie"
    climatologie = "climatologie"
    botanique = "botanique"
    sylviculture = "sylviculture"
    dynamique_peuplements = "dynamique_des_peuplements"
    conservation = "conservation"
    inventaire = "inventaire"
    amenagement = "amenagement"
    risques = "risques"


class VersionEntry(BaseModel):
    """Entrée d'historique de version (CON-010 — aucune connaissance supprimée silencieusement)."""
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1, description="Numéro de version")
    date: datetime = Field(description="Date de cette version (ISO 8601)")
    justification: str = Field(min_length=1, max_length=2000, description="Pourquoi cette révision")
    rfc_reference: str | None = Field(
        default=None, max_length=50, description="RFC associée si évolution gouvernée"
    )


class DomaineValidite(BaseModel):
    """Domaine de validité d'une connaissance (conditions d'application)."""
    model_config = ConfigDict(extra="forbid")

    parametre: str = Field(
        min_length=1, max_length=100, description="Ex. « pH », « altitude », « climat »"
    )
    minimum: float | None = Field(default=None, description="Valeur minimale (optionnel)")
    maximum: float | None = Field(default=None, description="Valeur maximale (optionnel)")
    unite: str | None = Field(default=None, max_length=50, description="Unité (optionnel)")


class RelationRef(BaseModel):
    """Référence vers une autre connaissance (KNOWLEDGE_GRAPH_SPECIFICATION.md)."""
    model_config = ConfigDict(extra="forbid")

    connaissance_id: UUID = Field(description="UUID de la connaissance liée")
    predicat: str = Field(
        min_length=1, max_length=100,
        description="Type de relation (est_adapte_a, influence, etc.)"
    )
    sens: str = Field(
        default="sortant", max_length=20,
        description="sortant|entrant|bidirectionnel"
    )


class KnowledgeObject(BaseModel):
    """Objet de connaissance — nœud du graphe (KNOWLEDGE_ENGINE.md §5, KNOWLEDGE_METHOD.md §2).

    Source unique de vérité pour tous les moteurs de raisonnement.
    Versionné (CON-010), traçable (CON-005), sourcé (S-1).
    """
    model_config = ConfigDict(extra="forbid")

    # Identité
    connaissance_id: UUID = Field(description="Identifiant stable et unique (UUID v7 recommandé)")

    # Classification
    type: KnowledgeType = Field(description="Type de connaissance")
    titre: str = Field(min_length=1, max_length=300, description="Titre court descriptif")
    description: str = Field(min_length=1, max_length=5000, description="Description en français")
    domaine_scientifique: DomaineScientifique = Field(description="Domaine S-6")

    # Contenu typé (structure libre selon le type — voir KNOWLEDGE_METHOD.md §3)
    contenu: dict[str, Any] = Field(description="Structure typée selon le type de connaissance")

    # Preuve et source (CON-002, S-1, S-2)
    evidence_level: EvidenceLevel = Field(description="Niveau de preuve A-F")
    source: SourceReference = Field(description="Source identifiable et vérifiable")
    statut: KnowledgeStatus = Field(description="Statut après qualification Evidence Engine")

    # Versionnement (CON-010)
    version: int = Field(ge=1, description="Version courante (commence à 1)")
    date_integration: datetime = Field(description="Date d'intégration dans le graphe (ISO 8601)")
    historique: list[VersionEntry] = Field(
        default_factory=list,
        max_length=1000,
        description="Historique des versions (CON-010)",
    )

    # Conditions d'application (optionnel)
    domaines_validite: list[DomaineValidite] = Field(
        default_factory=list,
        max_length=100,
        description="Conditions d'application",
    )

    # Métadonnées (optionnel)
    moteurs_consommateurs: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Moteurs qui utilisent cette connaissance",
    )
    relations: list[RelationRef] = Field(
        default_factory=list,
        max_length=200,
        description="Liens vers d'autres connaissances (livrable 304)",
    )
    mots_cles: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Mots-clés pour la recherche",
    )
    conflits: list[ConflitBibliographique] = Field(
        default_factory=list,
        max_length=100,
        description="Conflits avec d'autres sources (S-3)",
    )


class KnowledgeIngestRequest(BaseModel):
    """Requête d'ingestion d'une connaissance qualifiée dans le graphe.

    Le Knowledge Engine reçoit les connaissances au statut « accepte »
    depuis l'Evidence Engine (KNOWLEDGE_ENGINE.md §5).
    """
    model_config = ConfigDict(extra="forbid")

    # Champs de la connaissance qualifiée (depuis Evidence Engine)
    connaissance_id: UUID = Field(description="UUID de la connaissance (depuis Evidence Engine)")
    contenu_normalise: dict[str, Any] = Field(description="Contenu normalisé par l'Evidence Engine")

    # Métadonnées Knowledge Engine (ajoutées à l'ingestion)
    type: KnowledgeType = Field(description="Type de connaissance")
    titre: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=5000)
    domaine_scientifique: DomaineScientifique

    # Preuve et source (transmises depuis Evidence Engine)
    evidence_level: EvidenceLevel
    source: SourceReference
    statut: KnowledgeStatus

    # Optionnels
    domaines_validite: list[DomaineValidite] = Field(default_factory=list, max_length=100)
    moteurs_consommateurs: list[str] = Field(default_factory=list, max_length=20)
    relations: list[RelationRef] = Field(default_factory=list, max_length=200)
    mots_cles: list[str] = Field(default_factory=list, max_length=50)
    conflits: list[ConflitBibliographique] = Field(default_factory=list, max_length=100)


class KnowledgeQuery(BaseModel):
    """Requête sur le graphe de connaissances (KNOWLEDGE_ENGINE.md §5)."""
    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(description="Identifiant de la requête (UUID)")
    type: QueryType = Field(description="Type de requête")
    filtres: dict[str, Any] = Field(
        default_factory=dict,
        description="Filtres clé-valeur selon le type de requête",
    )
    evidence_min: EvidenceLevel | None = Field(
        default=None,
        description="Niveau de preuve minimum (filtre — None = tous niveaux)",
    )
    page: int = Field(default=1, ge=1, description="Page de pagination")
    page_size: int = Field(default=20, ge=1, le=100, description="Taille de page (max 100)")


class KnowledgeQueryResult(BaseModel):
    """Résultat d'une requête sur le graphe (KNOWLEDGE_ENGINE.md §5)."""
    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(description="Identifiant de la requête (UUID)")
    connaissances: list[KnowledgeObject] = Field(
        default_factory=list,
        max_length=100,
        description="Connaissances correspondantes (page courante)",
    )
    total: int = Field(ge=0, description="Nombre total de correspondances")
    version_graph: str = Field(description="Version du graphe au moment de la requête")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class KnowledgeRevisionRequest(BaseModel):
    """Requête de révision d'une connaissance existante (CON-010).

    La révision archive l'ancienne version dans l'historique et crée
    une nouvelle version. La connaissance n'est jamais supprimée.
    """
    model_config = ConfigDict(extra="forbid")

    connaissance_id: UUID = Field(description="UUID de la connaissance à réviser")
    justification: str = Field(min_length=1, max_length=2000, description="Pourquoi cette révision")
    rfc_reference: str | None = Field(default=None, max_length=50)

    # Champs modifiables (au moins un requis)
    nouveau_contenu: dict[str, Any] | None = Field(default=None, description="Nouveau contenu")
    nouveau_evidence_level: EvidenceLevel | None = Field(default=None)
    nouvelle_source: SourceReference | None = Field(default=None)
    nouveaux_domaines_validite: list[DomaineValidite] | None = Field(default=None, max_length=100)
