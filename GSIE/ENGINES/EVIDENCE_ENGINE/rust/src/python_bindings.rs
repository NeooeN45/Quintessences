//! Bindings PyO3 — expose l'Evidence Engine à Python.
//!
//! Conformément à ADR-0002 (TECHNOLOGY_STACK.md) :
//! - Sérialisation via serde (JSON string) — simple et robuste
//! - Limite de taille JSON pour prévenir le DoS (10 MB max)
//!
//! Usage Python :
//!   from gsie_evidence import EvidenceEngine
//!   result = EvidenceEngine.evaluate_json(submission_json_str)
//!   # result est une string JSON à désérialiser côté Python

use pyo3::prelude::*;
use serde_json;

use crate::engine::EvidenceEngine as RustEngine;
use crate::types::{RawKnowledgeSubmission, SourceReference};

/// Taille maximale du JSON entrant (10 MB) — anti-DoS.
const MAX_JSON_SIZE: usize = 10 * 1024 * 1024;

/// Module Python gsie_evidence.
#[pymodule]
fn gsie_evidence(m: &Bound<'_, PyModule>) -> PyResult<()> {
    /// Engine d'évaluation de la preuve (exposé à Python).
    #[pyclass]
    struct EvidenceEngine;

    #[pymethods]
    impl EvidenceEngine {
        /// Évalue une soumission de connaissance brute.
        ///
        /// Args:
        ///     submission_json: string JSON avec clés soumission_id, type_contenu,
        ///                      contenu, source_candidate, date_soumission, soumetteur
        ///
        /// Returns:
        ///     string JSON avec connaissance_id, evidence_level, statut, source, etc.
        #[staticmethod]
        fn evaluate_json(submission_json: String) -> PyResult<String> {
            // Valider la taille du JSON avant désérialisation (anti-DoS)
            if submission_json.len() > MAX_JSON_SIZE {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "JSON trop volumineux : {} octets (max : {} octets)",
                    submission_json.len(),
                    MAX_JSON_SIZE
                )));
            }

            // Désérialiser la soumission depuis JSON
            let submission: RawKnowledgeSubmission = serde_json::from_str(&submission_json)
                .map_err(|e| {
                    pyo3::exceptions::PyValueError::new_err(format!(
                        "JSON invalide : {e}"
                    ))
                })?;

            // Évaluer (le GIL est maintenu — l'évaluation est rapide, < 1ms)
            let result = RustEngine::evaluate(submission)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            // Sérialiser le résultat en JSON
            serde_json::to_string(&result)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
        }

        /// Évalue une soumission et retourne le niveau de preuve uniquement.
        ///
        /// Args:
        ///     submission_json: string JSON de la soumission
        ///
        /// Returns:
        ///     string : "A", "B", "C", "D", "E" ou "F"
        #[staticmethod]
        fn evaluate_level(submission_json: String) -> PyResult<String> {
            // Valider la taille du JSON avant désérialisation (anti-DoS)
            if submission_json.len() > MAX_JSON_SIZE {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "JSON trop volumineux : {} octets (max : {} octets)",
                    submission_json.len(),
                    MAX_JSON_SIZE
                )));
            }

            let submission: RawKnowledgeSubmission = serde_json::from_str(&submission_json)
                .map_err(|e| {
                    pyo3::exceptions::PyValueError::new_err(format!("JSON invalide : {e}"))
                })?;

            let result = RustEngine::evaluate(submission)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            Ok(result.evidence_level.to_string())
        }

        /// Version du moteur.
        #[staticmethod]
        fn version() -> &'static str {
            "0.1.0"
        }

        /// Évalue une soumission avec contexte (sources existantes + parent pour versionnement).
        ///
        /// Args :
        ///     submission_json: string JSON de la soumission
        ///     existing_sources_json: string JSON d'une liste de SourceReference (peut être "[]")
        ///     parent_version: int ou None (version de la connaissance parente)
        ///
        /// Returns :
        ///     string JSON avec connaissance_id, evidence_level, statut, source, conflits, version, etc.
        #[staticmethod]
        #[pyo3(signature = (submission_json, existing_sources_json = "[]".to_string(), parent_version = None))]
        fn evaluate_with_context(
            submission_json: String,
            existing_sources_json: String,
            parent_version: Option<u32>,
        ) -> PyResult<String> {
            // Valider la taille du JSON avant désérialisation (anti-DoS)
            if submission_json.len() > MAX_JSON_SIZE {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "JSON trop volumineux : {} octets (max : {} octets)",
                    submission_json.len(),
                    MAX_JSON_SIZE
                )));
            }
            if existing_sources_json.len() > MAX_JSON_SIZE {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "existing_sources JSON trop volumineux : {} octets (max : {} octets)",
                    existing_sources_json.len(),
                    MAX_JSON_SIZE
                )));
            }

            let submission: RawKnowledgeSubmission = serde_json::from_str(&submission_json)
                .map_err(|e| {
                    pyo3::exceptions::PyValueError::new_err(format!("JSON invalide : {e}"))
                })?;

            let existing_sources: Vec<SourceReference> =
                serde_json::from_str(&existing_sources_json)
                    .map_err(|e| {
                        pyo3::exceptions::PyValueError::new_err(format!(
                            "existing_sources JSON invalide : {e}"
                        ))
                    })?;

            let result = RustEngine::evaluate_with_context(
                submission,
                &existing_sources,
                parent_version,
            )
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

            serde_json::to_string(&result)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
        }

        /// Détecte les conflits bibliographiques entre une source et des sources existantes.
        ///
        /// Args :
        ///     candidate_json: string JSON d'une SourceReference
        ///     existing_sources_json: string JSON d'une liste de SourceReference
        ///
        /// Returns :
        ///     string JSON d'une liste de ConflitBibliographique (vide si aucun conflit)
        #[staticmethod]
        fn detect_conflicts(
            candidate_json: String,
            existing_sources_json: String,
        ) -> PyResult<String> {
            if candidate_json.len() > MAX_JSON_SIZE || existing_sources_json.len() > MAX_JSON_SIZE {
                return Err(pyo3::exceptions::PyValueError::new_err("JSON trop volumineux"));
            }

            let candidate: SourceReference = serde_json::from_str(&candidate_json)
                .map_err(|e| {
                    pyo3::exceptions::PyValueError::new_err(format!("candidate JSON invalide : {e}"))
                })?;

            let existing: Vec<SourceReference> = serde_json::from_str(&existing_sources_json)
                .map_err(|e| {
                    pyo3::exceptions::PyValueError::new_err(format!(
                        "existing_sources JSON invalide : {e}"
                    ))
                })?;

            let conflits = RustEngine::detect_conflicts(&candidate, &existing);
            serde_json::to_string(&conflits)
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
        }
    }

    m.add_class::<EvidenceEngine>()?;
    m.add("__doc__", "GSIE Evidence Engine — évaluation de la qualité scientifique (Rust + PyO3)")?;
    m.add("EVIDENCE_LEVELS", vec!["A", "B", "C", "D", "E", "F"])?;

    Ok(())
}
