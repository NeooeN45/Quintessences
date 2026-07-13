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
    ConflitBibliographique, ContentType, EvidenceLevel, KnowledgeStatus,
    QualifiedKnowledge, RawKnowledgeSubmission, SourceReference, SourceType,
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
    /// 3. Détection de conflits bibliographiques (si sources existantes fournies)
    /// 4. Détermination du statut (accepte / quarantine / refuse)
    /// 5. Génération de l'UUID, version et timestamp
    ///
    /// Versionnement : si `parent_version` est fourni, la nouvelle version
    /// est parent_version + 1 (lien parent-enfant pour traçabilité CON-005).
    pub fn evaluate(submission: RawKnowledgeSubmission) -> Result<QualifiedKnowledge, EvidenceError> {
        Self::evaluate_with_context(submission, &[], None)
    }

    /// Évalue une soumission avec contexte : sources existantes + parent pour versionnement.
    ///
    /// Args :
    /// - `existing_sources` : sources déjà qualifiées pour détecter les conflits
    /// - `parent_version` : version de la connaissance parente (None = nouvelle, version 1)
    pub fn evaluate_with_context(
        submission: RawKnowledgeSubmission,
        existing_sources: &[SourceReference],
        parent_version: Option<u32>,
    ) -> Result<QualifiedKnowledge, EvidenceError> {
        // 1. Validation
        Self::validate_source(&submission)?;
        Self::validate_content(&submission)?;

        // 2. Attribution du niveau de preuve
        let evidence_level = Self::determine_evidence_level(&submission);

        // 3. Détection de conflits bibliographiques
        let conflits = Self::detect_conflicts(&submission.source_candidate, existing_sources);

        // 4. Détermination du statut (conflit non résolvable → F)
        let statut = if !conflits.is_empty() {
            KnowledgeStatus::Refuse
        } else {
            Self::determine_status(evidence_level)
        };

        // 5. Versionnement : incrément si parent fourni
        let version = parent_version.map_or(1, |pv| pv + 1);

        // 6. Construction de la connaissance qualifiée
        Ok(QualifiedKnowledge {
            connaissance_id: Uuid::new_v4(),
            contenu_normalise: submission.contenu,
            evidence_level,
            source: submission.source_candidate,
            version,
            date_qualification: Utc::now(),
            conflits,
            statut,
        })
    }

    /// Détecte les conflits bibliographiques entre une source candidate et des sources existantes.
    ///
    /// Un conflit est détecté quand :
    /// - Deux sources partagent la même référence (DOI, URL) mais ont des types différents
    ///   (ex: peer_reviewed vs expert_identifie — indique une désinformation potentielle)
    /// - Deux sources ont le même auteur + même date mais des références différentes
    ///   (indique une attribution erronée)
    ///
    /// Args :
    /// - `candidate` : source candidate à vérifier
    /// - `existing` : sources déjà qualifiées dans la base
    ///
    /// Returns : liste des conflits détectés (vide si aucun)
    pub fn detect_conflicts(
        candidate: &SourceReference,
        existing: &[SourceReference],
    ) -> Vec<ConflitBibliographique> {
        let mut conflits = Vec::new();

        for source in existing {
            // Conflit type 1 : même référence, type de source différent
            if Self::normalize_reference(&candidate.reference)
                == Self::normalize_reference(&source.reference)
                && candidate.type_source != source.type_source
            {
                conflits.push(ConflitBibliographique {
                    source_a: candidate.clone(),
                    source_b: source.clone(),
                    description: format!(
                        "Référence identique ({}) mais type de source divergent : {:?} vs {:?}",
                        candidate.reference, candidate.type_source, source.type_source
                    ),
                });
                continue;
            }

            // Conflit type 2 : même auteur + même date, références différentes
            if candidate.auteur.eq_ignore_ascii_case(&source.auteur)
                && candidate.date_publication.is_some()
                && candidate.date_publication == source.date_publication
                && Self::normalize_reference(&candidate.reference)
                    != Self::normalize_reference(&source.reference)
            {
                conflits.push(ConflitBibliographique {
                    source_a: candidate.clone(),
                    source_b: source.clone(),
                    description: format!(
                        "Même auteur ({}) et date ({}) mais références différentes — attribution erronée possible",
                        candidate.auteur,
                        candidate.date_publication.as_ref().unwrap()
                    ),
                });
            }
        }

        conflits
    }

    /// Normalise une référence pour comparaison (lowercase, trim, suppression espaces superflus).
    fn normalize_reference(reference: &str) -> String {
        reference.trim().to_lowercase().replace(' ', "")
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
