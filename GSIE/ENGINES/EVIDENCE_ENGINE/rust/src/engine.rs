//! Moteur d'évaluation de la preuve — cœur de l'Evidence Engine.
//!
//! Responsabilité : évaluer la qualité scientifique d'une soumission
//! et lui attribuer un niveau de preuve (A-F) selon EVIDENCE_FRAMEWORK.md.
//!
//! Algorithme : matrice de décision basée sur
//! 1. Le type de source (peer-reviewed > référentiel > expert > observation)
//! 2. Le type de contenu (cohérence avec la source)
//! 3. La présence de conflits bibliographiques
//! 4. La robustesse (version, date, référence)
//!
//! Conforme à CON-002 : la science avant tout.
//! Conforme à CON-001 : l'IA assiste, ne décide jamais (le statut quarantine
//! laisse le décideur humain trancher).

use chrono::Utc;
use uuid::Uuid;

use crate::types::{
    ContentType, EvidenceLevel, KnowledgeStatus, QualifiedKnowledge,
    RawKnowledgeSubmission, SourceType,
};

/// Erreurs de l'Evidence Engine.
#[derive(Debug, thiserror::Error)]
pub enum EvidenceError {
    #[error("source invalide : {0}")]
    InvalidSource(String),
    #[error("contenu vide")]
    EmptyContent,
}

/// Moteur d'évaluation de la preuve.
pub struct EvidenceEngine;

impl EvidenceEngine {
    /// Évalue une soumission de connaissance et retourne une connaissance qualifiée.
    ///
    /// Pipeline :
    /// 1. Validation de la source (non vide, référence présente)
    /// 2. Attribution du niveau de preuve (matrice source × contenu)
    /// 3. Détermination du statut (accepte / quarantine / refuse)
    /// 4. Génération de l'UUID et timestamp
    pub fn evaluate(submission: RawKnowledgeSubmission) -> Result<QualifiedKnowledge, EvidenceError> {
        // 1. Validation
        Self::validate_source(&submission)?;
        Self::validate_content(&submission)?;

        // 2. Attribution du niveau de preuve
        let evidence_level = Self::determine_evidence_level(&submission);

        // 3. Détermination du statut
        let statut = Self::determine_status(evidence_level);

        // 4. Construction de la connaissance qualifiée
        Ok(QualifiedKnowledge {
            connaissance_id: Uuid::new_v4(),
            contenu_normalise: submission.contenu,
            evidence_level,
            source: submission.source_candidate,
            version: 1,
            date_qualification: Utc::now(),
            conflits: Vec::new(),
            statut,
        })
    }

    /// Valide que la source a une référence et un auteur non vides.
    fn validate_source(submission: &RawKnowledgeSubmission) -> Result<(), EvidenceError> {
        if submission.source_candidate.auteur.trim().is_empty() {
            return Err(EvidenceError::InvalidSource("auteur manquant".into()));
        }
        if submission.source_candidate.reference.trim().is_empty() {
            return Err(EvidenceError::InvalidSource("référence manquante".into()));
        }
        Ok(())
    }

    /// Valide que le contenu n'est pas vide (null ou object vide).
    fn validate_content(submission: &RawKnowledgeSubmission) -> Result<(), EvidenceError> {
        if submission.contenu.is_null()
            || (submission.contenu.is_object() && submission.contenu.as_object().map_or(false, |o| o.is_empty()))
        {
            return Err(EvidenceError::EmptyContent);
        }
        Ok(())
    }

    /// Détermine le niveau de preuve selon la matrice source × contenu.
    ///
    /// Matrice de décision (EVIDENCE_FRAMEWORK.md) :
    ///
    /// | Source \ Contenu    | Publication | Référentiel | Expert | Observation |
    /// |---------------------|-------------|-------------|--------|-------------|
    /// | Peer-reviewed       | B           | B           | C      | C           |
    /// | Référentiel officiel| B           | A*          | D      | E           |
    /// | Expert identifié    | D           | D           | D      | E           |
    /// | Observation terrain | E           | E           | E      | E           |
    ///
    /// A* : un référentiel officiel avec contenu référentiel = niveau A
    ///      (consensus institutionnel reproductible)
    ///
    /// Notes :
    /// - Le niveau A (méta-analyse) nécessite un corpus, non une seule source.
    ///   Une seule source peer-reviewed = B maximum.
    /// - Le niveau F est attribué en cas de conflit (géré par detect_conflicts).
    fn determine_evidence_level(submission: &RawKnowledgeSubmission) -> EvidenceLevel {
        let source = &submission.source_candidate.type_source;
        let content = &submission.type_contenu;

        match (source, content) {
            // Référentiel officiel + contenu référentiel = A (consensus institutionnel)
            (SourceType::ReferentielOfficiel, ContentType::Referentiel) => EvidenceLevel::A,
            // Peer-reviewed + publication = B (établi)
            (SourceType::PeerReviewed, ContentType::Publication) => EvidenceLevel::B,
            // Référentiel officiel + publication = B
            (SourceType::ReferentielOfficiel, ContentType::Publication) => EvidenceLevel::B,
            // Peer-reviewed + référentiel = B
            (SourceType::PeerReviewed, ContentType::Referentiel) => EvidenceLevel::B,
            // Peer-reviewed + expert = C (probable, domaine partiel)
            (SourceType::PeerReviewed, ContentType::Expert) => EvidenceLevel::C,
            // Peer-reviewed + observation = C
            (SourceType::PeerReviewed, ContentType::Observation) => EvidenceLevel::C,
            // Référentiel officiel + expert = D
            (SourceType::ReferentielOfficiel, ContentType::Expert) => EvidenceLevel::D,
            // Référentiel officiel + observation = E
            (SourceType::ReferentielOfficiel, ContentType::Observation) => EvidenceLevel::E,
            // Expert identifié + tout = D (sauf observation = E)
            (SourceType::ExpertIdentifie, ContentType::Publication) => EvidenceLevel::D,
            (SourceType::ExpertIdentifie, ContentType::Referentiel) => EvidenceLevel::D,
            (SourceType::ExpertIdentifie, ContentType::Expert) => EvidenceLevel::D,
            (SourceType::ExpertIdentifie, ContentType::Observation) => EvidenceLevel::E,
            // Observation terrain + tout = E
            (SourceType::ObservationTerrain, _) => EvidenceLevel::E,
        }
    }

    /// Détermine le statut de la connaissance selon son niveau de preuve.
    ///
    /// - A, B, C → accepte (niveau suffisant pour intégration)
    /// - D, E    → quarantine (validation humaine requise — CON-001)
    /// - F       → refuse (conflit non résolvable)
    fn determine_status(level: EvidenceLevel) -> KnowledgeStatus {
        match level {
            EvidenceLevel::A | EvidenceLevel::B | EvidenceLevel::C => KnowledgeStatus::Accepte,
            EvidenceLevel::D | EvidenceLevel::E => KnowledgeStatus::Quarantine,
            EvidenceLevel::F => KnowledgeStatus::Refuse,
        }
    }
}
