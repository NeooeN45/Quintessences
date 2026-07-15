"""Schémas Pydantic pour l'Evidence Engine.

Conforme à ENGINE_INTERFACE_CONTRACTS.md :
- RawKnowledgeSubmission (entrée)
- QualifiedKnowledge (sortie)
- EvidenceLevel (A-F)
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceType(StrEnum):
    """Type de source scientifique (EVIDENCE_FRAMEWORK.md)."""
    peer_reviewed = "peer_reviewed"
    referentiel_officiel = "referentiel_officiel"
    expert_identifie = "expert_identifie"
    observation_terrain = "observation_terrain"


class ContentType(StrEnum):
    """Type de contenu soumis."""
    publication = "publication"
    referentiel = "referentiel"
    expert = "expert"
    observation = "observation"


class EvidenceLevel(StrEnum):
    """Niveau de preuve scientifique (CON-002). A=meilleur, F=pire."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class KnowledgeStatus(StrEnum):
    """Statut de la connaissance après qualification."""
    accepte = "accepte"
    quarantine = "quarantine"
    refuse = "refuse"


class SourceReference(BaseModel):
    """Référence à une source scientifique."""
    model_config = ConfigDict(extra="forbid")

    type_source: SourceType
    auteur: str = Field(min_length=1, max_length=255, description="Auteur ou organisme")
    date_publication: str | None = Field(default=None, max_length=50)
    reference: str = Field(min_length=1, max_length=500, description="DOI, URL, citation ou code")
    version_source: str | None = Field(default=None, max_length=100)


class RawKnowledgeSubmission(BaseModel):
    """Soumission de connaissance brute — entrée de l'Evidence Engine."""
    model_config = ConfigDict(extra="forbid")

    soumission_id: UUID
    type_contenu: ContentType
    contenu: dict[str, Any] = Field(description="Structure libre (texte, tableau, mesure)")
    source_candidate: SourceReference
    date_soumission: datetime
    soumetteur: str = Field(min_length=1, max_length=255)


class ConflitBibliographique(BaseModel):
    """Conflit entre deux sources (CON-002)."""
    model_config = ConfigDict(extra="forbid")

    source_a: SourceReference
    source_b: SourceReference
    description: str = Field(min_length=1, max_length=5000)


class QualifiedKnowledge(BaseModel):
    """Connaissance qualifiée — sortie de l'Evidence Engine."""
    model_config = ConfigDict(extra="forbid")

    connaissance_id: UUID
    contenu_normalise: dict[str, Any]
    evidence_level: EvidenceLevel
    source: SourceReference
    version: int = Field(ge=1)
    date_qualification: datetime
    conflits: list[ConflitBibliographique] = Field(default_factory=list, max_length=100)
    statut: KnowledgeStatus
