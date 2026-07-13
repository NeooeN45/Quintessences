//! GSIE Evidence Engine — évaluation de la qualité scientifique.
//!
//! Cœur Rust exposé à Python via PyO3 (ADR-0002).
//! Responsabilité : attribuer un niveau de preuve (A-F) à chaque connaissance.
//! Conforme à CON-002 (la science avant tout) et CON-001 (l'IA assiste).

pub mod engine;
pub mod python_bindings;
pub mod types;

#[cfg(test)]
mod tests;

pub use engine::{EvidenceEngine, EvidenceError};
pub use types::{
    ConflitBibliographique, ContentType, EvidenceLevel, KnowledgeStatus,
    QualifiedKnowledge, RawKnowledgeSubmission, SourceReference, SourceType,
};
