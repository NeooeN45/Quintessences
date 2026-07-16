"""Wrapper Python — appelle le cœur Rust (gsie_evidence) via PyO3.

Si le module Rust n'est pas installé (dev sans Rust), un fallback
Python est utilisé. En production, le module Rust compilé est requis.

Fonctionnalités exposées :
- evaluate : évaluation simple (source unique, version 1)
- evaluate_with_context : évaluation avec sources existantes + versionnement
- detect_conflicts : détection de conflits bibliographiques
"""

from typing import cast

from gsie_api.core.config import get_settings
from gsie_api.core.logging import get_logger
from gsie_api.engines.evidence.schemas import (
    ConflitBibliographique,
    KnowledgeStatus,
    QualifiedKnowledge,
    RawKnowledgeSubmission,
    SourceReference,
)

logger = get_logger("gsie_api.evidence.wrapper")
_settings = get_settings()

# Tentative d'import du module Rust compilé
try:
    import gsie_evidence as _rust_engine  # type: ignore[import-untyped]

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


def evaluate_with_context(
    submission: RawKnowledgeSubmission,
    existing_sources: list[SourceReference] | None = None,
    parent_version: int | None = None,
) -> QualifiedKnowledge:
    """Évalue une soumission avec contexte (sources existantes + versionnement).

    Args:
        submission: Soumission de connaissance brute.
        existing_sources: Sources déjà qualifiées pour détecter les conflits.
        parent_version: Version de la connaissance parente (None = nouvelle).

    Returns:
        Connaissance qualifiée avec conflits détectés et version incrémentée.
    """
    sources = existing_sources or []
    if sources and not _settings.evidence_experimental_conflicts_enabled:
        logger.warning("experimental_conflict_detection_disabled")
        sources = []
    if _RUST_AVAILABLE:
        return _evaluate_with_context_rust(submission, sources, parent_version)
    return _evaluate_python_fallback(submission, sources, parent_version)


def detect_conflicts(
    candidate: SourceReference,
    existing: list[SourceReference],
) -> list[ConflitBibliographique]:
    """Détecte les conflits bibliographiques entre une source et des sources existantes.

    Args:
        candidate: Source candidate à vérifier.
        existing: Sources déjà qualifiées dans la base.

    Returns:
        Liste des conflits détectés (vide si aucun).
    """
    if _RUST_AVAILABLE:
        return _detect_conflicts_rust(candidate, existing)
    return _detect_conflicts_python(candidate, existing)


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


def _evaluate_with_context_rust(
    submission: RawKnowledgeSubmission,
    existing_sources: list[SourceReference],
    parent_version: int | None,
) -> QualifiedKnowledge:
    """Évaluation avec contexte via le cœur Rust (PyO3)."""
    try:
        submission_json = submission.model_dump_json()
        sources_json = f"[{','.join(s.model_dump_json() for s in existing_sources)}]"
        result_json = _rust_engine.EvidenceEngine.evaluate_with_context(
            submission_json, sources_json, parent_version
        )
        return QualifiedKnowledge.model_validate_json(result_json)
    except Exception as exc:
        logger.error(
            "rust_engine_context_evaluation_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        logger.warning("falling_back_to_python_evaluation")
        return _evaluate_python_fallback(submission, existing_sources, parent_version)


def _detect_conflicts_rust(
    candidate: SourceReference,
    existing: list[SourceReference],
) -> list[ConflitBibliographique]:
    """Détection de conflits via le cœur Rust (PyO3)."""
    try:
        candidate_json = candidate.model_dump_json()
        existing_json = f"[{','.join(s.model_dump_json() for s in existing)}]"
        result_json = _rust_engine.EvidenceEngine.detect_conflicts(candidate_json, existing_json)
        import json

        raw = json.loads(result_json)
        return [ConflitBibliographique.model_validate(c) for c in raw]
    except Exception as exc:
        logger.error(
            "rust_detect_conflicts_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return _detect_conflicts_python(candidate, existing)


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


def _evaluate_python_fallback(
    submission: RawKnowledgeSubmission,
    existing_sources: list[SourceReference] | None = None,
    parent_version: int | None = None,
) -> QualifiedKnowledge:
    """Évaluation via Python (fallback si Rust non disponible).

    Logique identique au cœur Rust (engine.rs) — matrice de décision A-F.
    Inclut la détection de conflits et le versionnement parent-enfant.
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from gsie_api.engines.evidence.schemas import EvidenceLevel

    sources = existing_sources or []
    source_type = submission.source_candidate.type_source.value
    content_type = submission.type_contenu.value
    level_str = _DECISION_MATRIX.get((source_type, content_type), "F")

    # Détection de conflits (identique au cœur Rust)
    conflits = _detect_conflicts_python(submission.source_candidate, sources)

    # Statut : refuse si conflit, sinon selon le niveau
    status = KnowledgeStatus.refuse if conflits else _STATUS_MAP[level_str]

    # Versionnement : incrément si parent fourni
    version = parent_version + 1 if parent_version is not None else 1

    return QualifiedKnowledge(
        connaissance_id=uuid4(),
        contenu_normalise=submission.contenu,
        evidence_level=EvidenceLevel(level_str),
        source=submission.source_candidate,
        version=version,
        date_qualification=datetime.now(UTC),
        conflits=conflits,
        statut=status,
    )


def _detect_conflicts_python(
    candidate: SourceReference,
    existing: list[SourceReference],
) -> list[ConflitBibliographique]:
    """Détection de conflits bibliographiques (fallback Python).

    Logique identique au cœur Rust (engine.rs::detect_conflicts) :
    - Conflit type 1 : même référence normalisée, type de source différent
    - Conflit type 2 : même auteur (case-insensitive) + même date, références différentes
    """
    conflits: list[ConflitBibliographique] = []

    def _normalize(ref: str) -> str:
        return ref.strip().lower().replace(" ", "")

    candidate_ref = _normalize(candidate.reference)

    for source in existing:
        source_ref = _normalize(source.reference)

        # Conflit type 1 : même référence, type différent
        if candidate_ref == source_ref and candidate.type_source != source.type_source:
            conflits.append(
                ConflitBibliographique(
                    source_a=candidate,
                    source_b=source,
                    description=(
                        f"Référence identique ({candidate.reference}) mais type de source "
                        f"divergent : {candidate.type_source.value} vs {source.type_source.value}"
                    ),
                )
            )
            continue

        # Conflit type 2 : même auteur + même date, références différentes
        if (
            candidate.auteur.lower() == source.auteur.lower()
            and candidate.date_publication is not None
            and candidate.date_publication == source.date_publication
            and candidate_ref != source_ref
        ):
            conflits.append(
                ConflitBibliographique(
                    source_a=candidate,
                    source_b=source,
                    description=(
                        f"Même auteur ({candidate.auteur}) et date "
                        f"({candidate.date_publication}) mais références différentes — "
                        f"attribution erronée possible"
                    ),
                )
            )

    return conflits


def is_rust_available() -> bool:
    """Retourne True si le moteur Rust compilé est disponible."""
    return _RUST_AVAILABLE


def engine_version() -> str:
    """Retourne la version du moteur (Rust ou fallback)."""
    if _RUST_AVAILABLE:
        return cast("str", _rust_engine.EvidenceEngine.version())
    return "0.1.0-python-fallback"
