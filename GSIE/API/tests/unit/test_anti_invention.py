"""Tests unitaires — garde anti-invention RFC-0014.

RFC-0014 §3.2 : « L'IA assiste, ne décide jamais. » Les données
produites par un LLM doivent être marquées `evidence_level = D` +
`quarantine`, indépendamment de la matrice de décision de l'Evidence
Engine.

Ces tests vérifient que :
1. Une soumission dont l'auteur contient "Claude" est détectée AI-sourced.
2. Une soumission dont la référence contient "treekipedia" est détectée.
3. Une soumission humaine (auteur "Rameau 2008") n'est PAS détectée.
4. Une donnée AI-sourced qualifiée à B par la matrice est forcée à D + quarantine.
5. Une donnée AI-sourced qualifiée à F reste à F (refus — on ne relève jamais).
6. Une donnée AI-sourced qualifiée à D reste à D mais passe en quarantine.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from gsie_api.engines.evidence.anti_invention import (
    appliquer_garde_anti_invention,
    est_ai_sourced,
)
from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    KnowledgeStatus,
    QualifiedKnowledge,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)


def _source(auteur: str, reference: str, version: str | None = None) -> SourceReference:
    """Construit une SourceReference pour les tests."""
    return SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur=auteur,
        reference=reference,
        version_source=version,
    )


def _submission(source: SourceReference) -> RawKnowledgeSubmission:
    """Construit une soumission de test."""
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=ContentType.publication,
        contenu={"test": True},
        source_candidate=source,
        date_soumission=datetime.now(UTC),
        soumetteur="test",
    )


def _qualified(
    level: EvidenceLevel = EvidenceLevel.B,
    statut: KnowledgeStatus = KnowledgeStatus.accepte,
    source: SourceReference | None = None,
) -> QualifiedKnowledge:
    """Construit une connaissance qualifiée de test."""
    return QualifiedKnowledge(
        connaissance_id=uuid4(),
        contenu_normalise={"test": True},
        evidence_level=level,
        source=source or _source("Test", "ref"),
        version=1,
        date_qualification=datetime.now(UTC),
        conflits=[],
        statut=statut,
    )


# --- Détection est_ai_sourced ---


def test_should_detect_claude_in_author() -> None:
    """Un auteur contenant 'Claude' doit être détecté comme AI-sourced."""
    source = _source(auteur="Claude Code CLI", reference="doi:10.1234/test")
    submission = _submission(source)

    assert est_ai_sourced(submission) is True


def test_should_detect_treekipedia_in_reference() -> None:
    """Une référence contenant 'treekipedia' doit être détectée."""
    source = _source(auteur="Silvi", reference="treekipedia.org/insight/123")
    submission = _submission(source)

    assert est_ai_sourced(submission) is True


def test_should_detect_gpt_in_version() -> None:
    """Une version contenant 'gpt-4' doit être détectée."""
    source = _source(auteur="OpenAI", reference="doi:10.1234/test", version="gpt-4-turbo")
    submission = _submission(source)

    assert est_ai_sourced(submission) is True


def test_should_not_detect_human_source() -> None:
    """Une source humaine (Rameau 2008) ne doit PAS être détectée."""
    source = _source(auteur="Rameau et al.", reference="doi:10.1234/rameau")
    submission = _submission(source)

    assert est_ai_sourced(submission) is False


def test_should_not_detect_official_source() -> None:
    """Une source officielle IGN ne doit PAS être détectée."""
    source = _source(auteur="IGN", reference="BD Forêt v2")
    submission = _submission(source)

    assert est_ai_sourced(submission) is False


# --- Garde appliquer_garde_anti_invention ---


def test_should_force_level_d_and_quarantine_when_matrix_gave_b() -> None:
    """Une donnée AI-sourced qualifiée à B doit être forcée à D + quarantine."""
    source = _source(auteur="Claude", reference="treekipedia.org/123")
    submission = _submission(source)
    qualified = _qualified(level=EvidenceLevel.B, statut=KnowledgeStatus.accepte, source=source)

    result = appliquer_garde_anti_invention(submission, qualified)

    assert result.evidence_level == EvidenceLevel.D
    assert result.statut == KnowledgeStatus.quarantine


def test_should_force_quarantine_when_matrix_gave_c() -> None:
    """Une donnée AI-sourced qualifiée à C (accepte) doit passer en quarantine."""
    source = _source(auteur="GPT-4", reference="doi:10.1234/test")
    submission = _submission(source)
    qualified = _qualified(level=EvidenceLevel.C, statut=KnowledgeStatus.accepte, source=source)

    result = appliquer_garde_anti_invention(submission, qualified)

    assert result.evidence_level == EvidenceLevel.D
    assert result.statut == KnowledgeStatus.quarantine


def test_should_not_raise_level_when_matrix_gave_f() -> None:
    """Une donnée AI-sourced qualifiée à F (refuse) reste à F — on ne relève jamais."""
    source = _source(auteur="Claude", reference="test")
    submission = _submission(source)
    qualified = _qualified(level=EvidenceLevel.F, statut=KnowledgeStatus.refuse, source=source)

    result = appliquer_garde_anti_invention(submission, qualified)

    assert result.evidence_level == EvidenceLevel.F
    assert result.statut == KnowledgeStatus.refuse


def test_should_force_quarantine_when_level_d_but_accepted() -> None:
    """Une donnée AI-sourced à D mais accepte doit passer en quarantine."""
    source = _source(auteur="LLM extract", reference="test")
    submission = _submission(source)
    qualified = _qualified(level=EvidenceLevel.D, statut=KnowledgeStatus.accepte, source=source)

    result = appliquer_garde_anti_invention(submission, qualified)

    assert result.evidence_level == EvidenceLevel.D
    assert result.statut == KnowledgeStatus.quarantine


def test_should_not_modify_human_qualified_knowledge() -> None:
    """Une donnée humaine qualifiée à B ne doit pas être modifiée."""
    source = _source(auteur="Rameau et al.", reference="doi:10.1234/rameau")
    submission = _submission(source)
    qualified = _qualified(level=EvidenceLevel.B, statut=KnowledgeStatus.accepte, source=source)

    result = appliquer_garde_anti_invention(submission, qualified)

    assert result.evidence_level == EvidenceLevel.B
    assert result.statut == KnowledgeStatus.accepte


def test_should_preserve_conflits_when_correcting() -> None:
    """La correction doit préserver les conflits détectés par l'Evidence Engine."""
    from gsie_api.engines.evidence.schemas import ConflitBibliographique

    source = _source(auteur="Claude", reference="test")
    submission = _submission(source)
    conflit = ConflitBibliographique(
        source_a=source,
        source_b=_source("Autre", "autre"),
        description="Conflit test",
    )
    qualified = _qualified(level=EvidenceLevel.B, source=source)
    qualified = qualified.model_copy(update={"conflits": [conflit]})

    result = appliquer_garde_anti_invention(submission, qualified)

    assert len(result.conflits) == 1
    assert result.conflits[0].description == "Conflit test"
