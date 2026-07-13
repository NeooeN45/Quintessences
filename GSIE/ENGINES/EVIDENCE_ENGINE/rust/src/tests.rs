//! Tests unitaires de l'Evidence Engine (cœur Rust).
//!
//! Convention : should_[expected]_when_[condition]

use chrono::Utc;
use serde_json::json;
use uuid::Uuid;

use crate::engine::{EvidenceEngine, EvidenceError};
use crate::types::{
    ContentType, EvidenceLevel, KnowledgeStatus, RawKnowledgeSubmission, SourceReference,
    SourceType,
};

/// Crée une soumission valide pour les tests.
fn make_submission(
    source_type: SourceType,
    content_type: ContentType,
) -> RawKnowledgeSubmission {
    RawKnowledgeSubmission {
        soumission_id: Uuid::new_v4(),
        type_contenu: content_type,
        contenu: json!({"title": "Test connaissance", "data": 42}),
        source_candidate: SourceReference {
            type_source: source_type,
            auteur: "IGN".to_string(),
            date_publication: Some("2024-01-15".to_string()),
            reference: "DOI:10.1234/test".to_string(),
            version_source: Some("1.0".to_string()),
        },
        date_soumission: Utc::now(),
        soumetteur: "test_user".to_string(),
    }
}

// --- Tests de validation ---

#[test]
fn should_return_error_when_author_empty() {
    let mut sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    sub.source_candidate.auteur = "   ".to_string();
    let result = EvidenceEngine::evaluate(sub);
    assert!(result.is_err());
    assert!(matches!(
        result.unwrap_err(),
        EvidenceError::InvalidSource(_)
    ));
}

#[test]
fn should_return_error_when_reference_empty() {
    let mut sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    sub.source_candidate.reference = "".to_string();
    let result = EvidenceEngine::evaluate(sub);
    assert!(result.is_err());
}

#[test]
fn should_return_error_when_content_null() {
    let mut sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    sub.contenu = json!(null);
    let result = EvidenceEngine::evaluate(sub);
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), EvidenceError::EmptyContent));
}

#[test]
fn should_return_error_when_content_empty_object() {
    let mut sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    sub.contenu = json!({});
    let result = EvidenceEngine::evaluate(sub);
    assert!(result.is_err());
}

// --- Tests de la matrice de décision (niveaux A-F) ---

#[test]
fn should_return_level_a_when_referentiel_officiel_and_referentiel() {
    let sub = make_submission(SourceType::ReferentielOfficiel, ContentType::Referentiel);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::A);
}

#[test]
fn should_return_level_b_when_peer_reviewed_and_publication() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::B);
}

#[test]
fn should_return_level_b_when_referentiel_officiel_and_publication() {
    let sub = make_submission(SourceType::ReferentielOfficiel, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::B);
}

#[test]
fn should_return_level_c_when_peer_reviewed_and_expert() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Expert);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::C);
}

#[test]
fn should_return_level_c_when_peer_reviewed_and_observation() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Observation);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::C);
}

#[test]
fn should_return_level_d_when_expert_identifie_and_publication() {
    let sub = make_submission(SourceType::ExpertIdentifie, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::D);
}

#[test]
fn should_return_level_d_when_expert_identifie_and_expert() {
    let sub = make_submission(SourceType::ExpertIdentifie, ContentType::Expert);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::D);
}

#[test]
fn should_return_level_e_when_expert_identifie_and_observation() {
    let sub = make_submission(SourceType::ExpertIdentifie, ContentType::Observation);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::E);
}

#[test]
fn should_return_level_e_when_observation_terrain_and_publication() {
    let sub = make_submission(SourceType::ObservationTerrain, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::E);
}

#[test]
fn should_return_level_e_when_observation_terrain_and_observation() {
    let sub = make_submission(SourceType::ObservationTerrain, ContentType::Observation);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.evidence_level, EvidenceLevel::E);
}

// --- Tests du statut ---

#[test]
fn should_return_accepte_when_level_a() {
    let sub = make_submission(SourceType::ReferentielOfficiel, ContentType::Referentiel);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.statut, KnowledgeStatus::Accepte);
}

#[test]
fn should_return_accepte_when_level_b() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.statut, KnowledgeStatus::Accepte);
}

#[test]
fn should_return_accepte_when_level_c() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Expert);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.statut, KnowledgeStatus::Accepte);
}

#[test]
fn should_return_quarantine_when_level_d() {
    let sub = make_submission(SourceType::ExpertIdentifie, ContentType::Expert);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.statut, KnowledgeStatus::Quarantine);
}

#[test]
fn should_return_quarantine_when_level_e() {
    let sub = make_submission(SourceType::ObservationTerrain, ContentType::Observation);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.statut, KnowledgeStatus::Quarantine);
}

// --- Tests de structure ---

#[test]
fn should_generate_uuid_when_evaluated() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert!(!result.connaissance_id.to_string().is_empty());
}

#[test]
fn should_set_version_to_1_when_newly_evaluated() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.version, 1);
}

#[test]
fn should_set_date_qualification_when_evaluated() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert!(result.date_qualification <= Utc::now());
}

#[test]
fn should_preserve_source_when_evaluated() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let original_ref = sub.source_candidate.reference.clone();
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.source.reference, original_ref);
}

#[test]
fn should_preserve_contenu_when_evaluated() {
    let sub = make_submission(SourceType::PeerReviewed, ContentType::Publication);
    let result = EvidenceEngine::evaluate(sub).unwrap();
    assert_eq!(result.contenu_normalise["data"], 42);
}

// --- Tests de l'enum EvidenceLevel ---

#[test]
fn should_order_evidence_levels_correctly() {
    assert!(EvidenceLevel::A > EvidenceLevel::B);
    assert!(EvidenceLevel::B > EvidenceLevel::C);
    assert!(EvidenceLevel::C > EvidenceLevel::D);
    assert!(EvidenceLevel::D > EvidenceLevel::E);
    assert!(EvidenceLevel::E > EvidenceLevel::F);
}

#[test]
fn should_display_evidence_level_as_uppercase_letter() {
    assert_eq!(EvidenceLevel::A.to_string(), "A");
    assert_eq!(EvidenceLevel::F.to_string(), "F");
}
