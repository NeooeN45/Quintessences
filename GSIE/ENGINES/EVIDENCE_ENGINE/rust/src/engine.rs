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

/// Taille maximale des chaînes entrantes (anti-DoS).
const MAX_STRING_LENGTH: usize = 10_000;

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
    /// 1. Validation de la source (non vide, référence présente, longueurs OK)
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

    /// Valide que la source a une référence et un auteur non vides et de longueur raisonnable.
    fn validate_source(submission: &RawKnowledgeSubmission) -> Result<(), EvidenceError> {
        let auteur = submission.source_candidate.auteur.trim();
        if auteur.is_empty() {
            return Err(EvidenceError::InvalidSource("auteur manquant".into()));
        }
        if auteur.len() > MAX_STRING_LENGTH {
            return Err(EvidenceError::InvalidSource("auteur trop long".into()));
        }

        let reference = submission.source_candidate.reference.trim();
        if reference.is_empty() {
            return Err(EvidenceError::InvalidSource("référence manquante".into()));
        }
        if reference.len() > MAX_STRING_LENGTH {
            return Err(EvidenceError::InvalidSource("référence trop longue".into()));
        }

        // Valider le soumetteur
        let soumetteur = submission.soumetteur.trim();
        if soumetteur.is_empty() {
            return Err(EvidenceError::InvalidSource("soumetteur manquant".into()));
        }
        if soumetteur.len() > MAX_STRING_LENGTH {
            return Err(EvidenceError::InvalidSource("soumetteur trop long".into()));
        }

        Ok(())
    }

    /// Valide que le contenu n'est pas vide (null ou object vide).
    fn validate_content(submission: &RawKnowledgeSubmission) -> Result<(), EvidenceError> {
        if submission.contenu.is_null()
            || (submission.contenu.is_object() && submission.contenu.as_object().is_some_and(|o| o.is_empty()))
        {
            return Err(EvidenceError::EmptyContent);
        }
        Ok(())
    }

    /// Détermine le niveau de preuve selon la matrice source × contenu.
    ///
    /// Matrice de décision conforme à EVIDENCE_FRAMEWORK.md (Validated) :
    /// Plafonds par catégorie de source (section 3.1) :
    /// - Peer-reviewed : plafond B (source unique), A si convergence ≥ 3 sources
    /// - Référentiel officiel : plafond B
    /// - Expert identifié : plafond D
    /// - Observation terrain : plafond F
    ///
    /// Le niveau A (consensus fort) exige la convergence multi-sources (≥ 3),
    /// non implémentée ici (évaluation source unique). Une seule source
    /// référentiel officiel = B maximum.
    ///
    /// | Source \ Contenu    | Publication | Référentiel | Expert | Observation |
    /// |---------------------|-------------|-------------|--------|-------------|
    /// | Peer-reviewed       | B           | B           | C      | C           |
    /// | Référentiel officiel| B           | B           | D      | D           |
    /// | Expert identifié    | D           | D           | D      | D           |
    /// | Observation terrain | F           | F           | F      | F           |
    ///
    /// Notes :
    /// - Le niveau A nécessite la convergence multi-sources (section 3.3 du framework).
    ///   Non attribuable par une évaluation source unique.
    /// - L'observation terrain est plafonnée à F (observation isolée, non recoupée).
    /// - Le niveau F est aussi attribué en cas de conflit (géré par detect_conflicts).
    fn determine_evidence_level(submission: &RawKnowledgeSubmission) -> EvidenceLevel {
        let source = &submission.source_candidate.type_source;
        let content = &submission.type_contenu;

        match (source, content) {
            // Peer-reviewed : plafond B (source unique)
            // Publication et référentiel = B (établi, reproductible)
            (SourceType::PeerReviewed, ContentType::Publication) => EvidenceLevel::B,
            (SourceType::PeerReviewed, ContentType::Referentiel) => EvidenceLevel::B,
            // Peer-reviewed + expert/observation = C (probable, domaine partiel)
            (SourceType::PeerReviewed, ContentType::Expert) => EvidenceLevel::C,
            (SourceType::PeerReviewed, ContentType::Observation) => EvidenceLevel::C,
            // Référentiel officiel : plafond B (validation institutionnelle)
            (SourceType::ReferentielOfficiel, ContentType::Publication) => EvidenceLevel::B,
            (SourceType::ReferentielOfficiel, ContentType::Referentiel) => EvidenceLevel::B,
            // Référentiel officiel + expert/observation = D (domaine partiel)
            (SourceType::ReferentielOfficiel, ContentType::Expert) => EvidenceLevel::D,
            (SourceType::ReferentielOfficiel, ContentType::Observation) => EvidenceLevel::D,
            // Expert identifié : plafond D (expertise non publiée)
            (SourceType::ExpertIdentifie, _) => EvidenceLevel::D,
            // Observation terrain : plafond F (observation isolée, non recoupée)
            (SourceType::ObservationTerrain, _) => EvidenceLevel::F,
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
