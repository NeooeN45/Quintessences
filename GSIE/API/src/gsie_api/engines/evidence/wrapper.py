"""Wrapper Python — appelle le cœur Rust (gsie_evidence) via PyO3.

Si le module Rust n'est pas installé (dev sans Rust), un fallback
Python est utilisé. En production, le module Rust compilé est requis.
"""

from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import (
    KnowledgeStatus,
    QualifiedKnowledge,
    RawKnowledgeSubmission,
)

logger = get_logger("gsie_api.evidence.wrapper")

# Tentative d'import du module Rust compilé
try:
    import gsie_evidence as _rust_engine

    _RUST_AVAILABLE = True
    logger.info("evidence_engine_rust_loaded", version=_rust_engine.EvidenceEngine.version())
except ImportError:  # pragma: no cover — Rust non compilé en dev
    _RUST_AVAILABLE = False
    logger.warning("evidence_engine_rust_not_available_fallback_python")


def evaluate(submission: RawKnowledgeSubmission) -> QualifiedKnowledge:
    """Évalue une soumission et retourne une connaissance qualifiée.

    Utilise le cœur Rust (gsie_evidence) si disponible, sinon fallback Python.

    Args:
        submission: Soumission de connaissance brute validée par Pydantic.

    Returns:
        Connaissance qualifiée avec niveau de preuve (A-F) et statut.
    """
    if _RUST_AVAILABLE:
        return _evaluate_rust(submission)
    return _evaluate_python_fallback(submission)


def _evaluate_rust(submission: RawKnowledgeSubmission) -> QualifiedKnowledge:
    """Évaluation via le cœur Rust (PyO3).

    Panic recovery : si l'appel Rust lève une exception (panic, erreur
    de sérialisation, erreur d'évaluation), on logge l'erreur et on
    fallback vers l'implémentation Python pour résilience (P0).
    """
    try:
        submission_json = submission.model_dump_json()
        result_json = _rust_engine.EvidenceEngine.evaluate_json(submission_json)
        return QualifiedKnowledge.model_validate_json(result_json)
    except Exception as exc:
        logger.error(
            "rust_engine_evaluation_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        logger.warning("falling_back_to_python_evaluation")
        return _evaluate_python_fallback(submission)


# --- Fallback Python (si Rust non installé) ---

# Matrice de décision (identique au cœur Rust — engine.rs)
# Conforme à EVIDENCE_FRAMEWORK.md (Validated) section 3.1 :
# - Peer-reviewed : plafond B (source unique), A si convergence ≥ 3 sources
# - Référentiel officiel : plafond B
# - Expert identifié : plafond D
# - Observation terrain : plafond F
# Le niveau A exige la convergence multi-sources (non attribuable ici).
_DECISION_MATRIX: dict[tuple[str, str], str] = {
    # (type_source, type_contenu) → evidence_level
    # Peer-reviewed : plafond B
    ("peer_reviewed", "publication"): "B",
    ("peer_reviewed", "referentiel"): "B",
    ("peer_reviewed", "expert"): "C",
    ("peer_reviewed", "observation"): "C",
    # Référentiel officiel : plafond B
    ("referentiel_officiel", "publication"): "B",
    ("referentiel_officiel", "referentiel"): "B",
    ("referentiel_officiel", "expert"): "D",
    ("referentiel_officiel", "observation"): "D",
    # Expert identifié : plafond D
    ("expert_identifie", "publication"): "D",
    ("expert_identifie", "referentiel"): "D",
    ("expert_identifie", "expert"): "D",
    ("expert_identifie", "observation"): "D",
    # Observation terrain : plafond F
    ("observation_terrain", "publication"): "F",
    ("observation_terrain", "referentiel"): "F",
    ("observation_terrain", "expert"): "F",
    ("observation_terrain", "observation"): "F",
}

_STATUS_MAP: dict[str, KnowledgeStatus] = {
    "A": KnowledgeStatus.accepte,
    "B": KnowledgeStatus.accepte,
    "C": KnowledgeStatus.accepte,
    "D": KnowledgeStatus.quarantine,
    "E": KnowledgeStatus.quarantine,
    "F": KnowledgeStatus.refuse,
}


def _evaluate_python_fallback(submission: RawKnowledgeSubmission) -> QualifiedKnowledge:
    """Évaluation via Python (fallback si Rust non disponible).

    Logique identique au cœur Rust (engine.rs) — matrice de décision A-F.
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from gsie_api.engines.evidence.schemas import EvidenceLevel

    source_type = submission.source_candidate.type_source.value
    content_type = submission.type_contenu.value
    level_str = _DECISION_MATRIX.get((source_type, content_type), "F")
    status = _STATUS_MAP[level_str]

    return QualifiedKnowledge(
        connaissance_id=uuid4(),
        contenu_normalise=submission.contenu,
        evidence_level=EvidenceLevel(level_str),
        source=submission.source_candidate,
        version=1,
        date_qualification=datetime.now(UTC),
        conflits=[],
        statut=status,
    )


def is_rust_available() -> bool:
    """Retourne True si le moteur Rust compilé est disponible."""
    return _RUST_AVAILABLE


def engine_version() -> str:
    """Retourne la version du moteur (Rust ou fallback)."""
    if _RUST_AVAILABLE:
        return _rust_engine.EvidenceEngine.version()
    return "0.1.0-python-fallback"
