"""Tests d'intégration — Evidence Engine (GSIE).

L'Evidence Engine évalue des soumissions de preuves via un cœur Rust (PyO3)
avec fallback Python. Il est stateless : aucune persistance en DB. Ces tests
vérifient l'intégration entre le moteur d'évaluation et la garde anti-invention
(RFC-0014), la matrice de décision A-F, le fallback Python, la détection de
conflits, le versionnement, et le déterminisme.

Le fixture ``db_session`` est présent pour le contexte d'intégration (PostgreSQL
réel via testcontainers) même si l'engine ne persiste pas — il valide que
l'évaluation fonctionne dans un environnement d'intégration complet.
"""

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.evidence.anti_invention import appliquer_garde_anti_invention
from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    KnowledgeStatus,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.evidence.wrapper import evaluate, evaluate_with_context
from tests.conftest import requires_docker

pytestmark = requires_docker


def _make_submission(
    source_type: SourceType = SourceType.peer_reviewed,
    content_type: ContentType = ContentType.publication,
    auteur: str = "IGN",
    reference: str = "DOI:10.1234/test",
) -> RawKnowledgeSubmission:
    """Crée une soumission valide pour les tests d'intégration."""
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=content_type,
        contenu={"title": "Test connaissance", "data": 42},
        source_candidate=SourceReference(
            type_source=source_type,
            auteur=auteur,
            date_publication="2024-01-15",
            reference=reference,
            version_source="1.0",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_user",
    )


# --- Matrice de décision A-F ---


async def should_return_level_b_when_peer_reviewed_publication(
    db_session: AsyncSession,
) -> None:
    """Peer-reviewed + publication doit donner niveau B (accepté).

    Plafond B pour source unique — le niveau A exige la convergence
    multi-sources (≥ 3) selon EVIDENCE_FRAMEWORK.md section 3.1.
    """
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.B
    assert result.statut == KnowledgeStatus.accepte


async def should_return_level_f_when_observation_terrain(
    db_session: AsyncSession,
) -> None:
    """Observation terrain doit donner niveau F (refusé).

    Observation isolée, non recoupée — plafond F selon EVIDENCE_FRAMEWORK.md.
    """
    sub = _make_submission(SourceType.observation_terrain, ContentType.observation)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.F
    assert result.statut == KnowledgeStatus.refuse


# --- Garde anti-invention (RFC-0014) ---


async def should_downgrade_to_d_when_ai_sourced_peer_reviewed(
    db_session: AsyncSession,
) -> None:
    """RFC-0014 : une soumission AI-sourced doit être déclassée à D (quarantine).

    Une soumission peer_reviewed + publication recevrait normalement B, mais
    la garde anti-invention détecte le marqueur AI (« Claude ») et force
    le niveau D avec quarantaine — validation humaine requise (CON-001).
    Sans cette garde, une extraction LLM contournait le garde-fou scientifique.
    """
    sub = _make_submission(
        SourceType.peer_reviewed,
        ContentType.publication,
        auteur="Claude 3.5 Sonnet",
        reference="DOI:10.1234/ai-extracted",
    )
    qualified = evaluate(sub)
    assert qualified.evidence_level == EvidenceLevel.B  # matrice avant garde

    corrected = appliquer_garde_anti_invention(sub, qualified)
    assert corrected.evidence_level == EvidenceLevel.D
    assert corrected.statut == KnowledgeStatus.quarantine


async def should_reject_when_source_candidate_missing(
    db_session: AsyncSession,
) -> None:
    """Une soumission sans source_candidate doit être rejetée par Pydantic.

    La source est obligatoire (CON-002) : une affirmation sans source n'est
    pas une preuve. La validation au niveau du schéma bloque l'ingestion
    avant même que l'engine ne l'évalue.
    """
    with pytest.raises(ValidationError, match="source_candidate"):
        RawKnowledgeSubmission(
            soumission_id=uuid4(),
            type_contenu=ContentType.publication,
            contenu={"data": 1},
            date_soumission=datetime.now(UTC),
            soumetteur="test_user",
        )


# --- Fallback Python ---


async def should_use_python_fallback_when_rust_unavailable(
    db_session: AsyncSession,
) -> None:
    """Le fallback Python doit produire les mêmes niveaux que le chemin nominal.

    Si le module Rust (gsie_evidence) n'est pas compilé, le wrapper bascule
    vers l'implémentation Python qui réplique la matrice de décision.
    """
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(wrapper_module, "_RUST_AVAILABLE", False):
        sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
        result = wrapper_module.evaluate(sub)
        assert result.evidence_level == EvidenceLevel.B
        assert result.statut == KnowledgeStatus.accepte


# --- Déterminisme ---


async def should_produce_same_evidence_level_when_evaluated_twice(
    db_session: AsyncSession,
) -> None:
    """L'évaluation est déterministe : même input → même niveau et statut.

    Les champs non-déterministes (connaissance_id, date_qualification) sont
    exclus — seuls les champs issus de la matrice de décision sont vérifiés.
    """
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    first = evaluate(sub)
    second = evaluate(sub)
    assert first.evidence_level == second.evidence_level
    assert first.statut == second.statut
    assert first.version == second.version
    assert first.contenu_normalise == second.contenu_normalise


# --- Détection de conflits + versionnement ---


async def should_refuse_when_conflict_detected_with_context(
    db_session: AsyncSession,
) -> None:
    """evaluate_with_context doit refuser quand un conflit bibliographique est détecté.

    Conflit type 1 : même référence normalisée, type de source divergent.
    Le statut passe à refuse — la connaissance ne peut pas être ingérée
    tant que le conflit n'est pas résolu.
    """
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(
        wrapper_module._settings,
        "evidence_experimental_conflicts_enabled",
        True,
    ):
        sub = _make_submission(
            SourceType.peer_reviewed,
            ContentType.publication,
            reference="DOI:10.1234/conflict",
        )
        existing = [
            SourceReference(
                type_source=SourceType.expert_identifie,
                auteur="Other",
                reference="DOI:10.1234/conflict",
            )
        ]
        result = evaluate_with_context(sub, existing_sources=existing)
        assert result.statut == KnowledgeStatus.refuse
        assert len(result.conflits) == 1


async def should_increment_version_when_parent_version_provided(
    db_session: AsyncSession,
) -> None:
    """evaluate_with_context doit incrémenter la version du parent.

    Versionnement parent-enfant : une réévaluation d'une connaissance
    existante (parent_version=3) produit une version 4, pas 1.
    """
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = evaluate_with_context(sub, parent_version=3)
    assert result.version == 4
