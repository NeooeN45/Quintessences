//! Types de données de l'Evidence Engine.
//!
//! Basés sur ENGINE_INTERFACE_CONTRACTS.md :
//! - RawKnowledgeSubmission (entrée)
//! - QualifiedKnowledge (sortie)
//! - EvidenceLevel (A-F)
//! - SourceReference, SourceType, ContentType

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Niveau de preuve scientifique (CON-002, EVIDENCE_FRAMEWORK.md).
///
/// Hiérarchie de A (consensus fort) à F (incertain/contesté).
/// A est le niveau le plus élevé (meilleur), F le plus bas.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum EvidenceLevel {
    /// Méta-analyse ou consensus fort — reproductible, multiple sources convergentes
    A,
    /// Établi — peer-reviewed, reproductible, domaine couvert
    B,
    /// Probable — peer-reviewed, domaine partiel ou limitations méthodologiques
    C,
    /// Expert identifié, non publié — autorité reconnue mais sans peer-review
    D,
    /// Observation terrain non publiée — donnée brute d'observateur qualifié
    E,
    /// Incertain ou contesté — conflit bibliographique ou méthode douteuse
    F,
}

impl EvidenceLevel {
    /// Retourne le rang numérique (A=6, F=1) — plus haut = meilleure preuve.
    fn rank(self) -> u8 {
        match self {
            EvidenceLevel::A => 6,
            EvidenceLevel::B => 5,
            EvidenceLevel::C => 4,
            EvidenceLevel::D => 3,
            EvidenceLevel::E => 2,
            EvidenceLevel::F => 1,
        }
    }
}

impl PartialOrd for EvidenceLevel {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for EvidenceLevel {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // A (rank 6) > B (rank 5) > ... > F (rank 1)
        self.rank().cmp(&other.rank())
    }
}

impl std::fmt::Display for EvidenceLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EvidenceLevel::A => write!(f, "A"),
            EvidenceLevel::B => write!(f, "B"),
            EvidenceLevel::C => write!(f, "C"),
            EvidenceLevel::D => write!(f, "D"),
            EvidenceLevel::E => write!(f, "E"),
            EvidenceLevel::F => write!(f, "F"),
        }
    }
}

/// Type de source scientifique (EVIDENCE_FRAMEWORK.md matrice de décision).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceType {
    /// Publication peer-reviewed (journal scientifique, conférence avec comité)
    PeerReviewed,
    /// Référentiel officiel (IGN, INPN, ONF, conventions internationales)
    ReferentielOfficiel,
    /// Expert identifié — autorité reconnue mais sans publication
    ExpertIdentifie,
    /// Observation terrain — donnée brute non publiée
    ObservationTerrain,
}

/// Type de contenu soumis.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContentType {
    /// Publication scientifique
    Publication,
    /// Référentiel (base de données officielle, norme)
    Referentiel,
    /// Dires d'expert
    Expert,
    /// Observation de terrain
    Observation,
}

/// Statut de la connaissance après qualification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum KnowledgeStatus {
    /// Acceptée — niveau de preuve suffisant, intégrée à GSIE
    Accepte,
    /// En quarantaine — niveau de preuve faible, nécessite validation humaine
    Quarantine,
    /// Refusée — source invalide ou conflit non résolvable
    Refuse,
}

/// Référence à une source scientifique (ENGINE_INTERFACE_CONTRACTS.md).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceReference {
    pub type_source: SourceType,
    pub auteur: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub date_publication: Option<String>,
    pub reference: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version_source: Option<String>,
}

/// Soumission de connaissance brute (entrée de l'Evidence Engine).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawKnowledgeSubmission {
    pub soumission_id: Uuid,
    pub type_contenu: ContentType,
    pub contenu: serde_json::Value,
    pub source_candidate: SourceReference,
    pub date_soumission: DateTime<Utc>,
    pub soumetteur: String,
}

/// Conflit bibliographique entre deux sources (CON-002).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConflitBibliographique {
    pub source_a: SourceReference,
    pub source_b: SourceReference,
    pub description: String,
}

/// Connaissance qualifiée (sortie de l'Evidence Engine).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualifiedKnowledge {
    pub connaissance_id: Uuid,
    pub contenu_normalise: serde_json::Value,
    pub evidence_level: EvidenceLevel,
    pub source: SourceReference,
    pub version: u32,
    pub date_qualification: DateTime<Utc>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub conflits: Vec<ConflitBibliographique>,
    pub statut: KnowledgeStatus,
}
