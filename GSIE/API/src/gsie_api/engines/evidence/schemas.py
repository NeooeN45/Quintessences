"""Schémas Pydantic pour l'Evidence Engine.

Conforme à ENGINE_INTERFACE_CONTRACTS.md :
- RawKnowledgeSubmission (entrée)
- QualifiedKnowledge (sortie)
- EvidenceLevel (A-F)

RFC-0016 §3.1, tranche 6/10 (dernière tranche du schéma forestier
spécialisé) : `EvidenceStatementCreate`/`Record` couvrent l'entité
`EvidenceStatement` — assertion atomique sourcée avec une localisation
précise obligatoire (page/table), renforçant `AssertionModel` +
`EvidenceAssessmentModel` (déjà existants,
`gsie_api.infrastructure.models.assertion`) sans les dupliquer.
`ConflictRecord` (l'autre entité de cette tranche) n'a pas de schéma
dédié ici : `ConflitBibliographique` (ce module) et `ConflictClusterModel`
(`gsie_api.infrastructure.models.governance`) couvrent déjà exactement
le même besoin (désaccord explicite entre sources, statut de
résolution) — les dupliquer violerait le principe « une
responsabilité, une table » déjà appliqué à `Intervention` (RFC-0016
tranche 3/10).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.infrastructure.models.enums import LifecycleStatus


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


class EvidenceStatementCreate(BaseModel):
    """Assertion atomique sourcée — jamais une citation vague.

    RFC-0016 §3.1 : `page_or_table` est obligatoire — une affirmation
    qui cite une source sans indiquer où (page, table, paragraphe) dans
    cette source n'est pas vérifiable, exactement le risque que
    RFC-0014 a nommé pour les données individuelles.
    """

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1, description="Assertion atomique, une seule affirmation")
    page_or_table: str = Field(
        min_length=1, max_length=200, description="Localisation précise dans la source citée"
    )
    territory_description: str | None = None
    evidence_level: EvidenceLevel
    source: SourceReference


class EvidenceStatementRecord(EvidenceStatementCreate):
    """`EvidenceStatementCreate` persistée — identifiant réel et statut de cycle de vie."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: LifecycleStatus
