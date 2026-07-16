"""Tests unitaires — Evidence Engine (wrapper Python → Rust).

Teste l'intégration du cœur Rust (gsie_evidence) via le wrapper Python.
Si le module Rust n'est pas disponible, teste le fallback Python.
"""

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.engines.evidence.schemas import (
    ContentType,
    EvidenceLevel,
    KnowledgeStatus,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)
from gsie_api.engines.evidence.wrapper import engine_version, evaluate, is_rust_available

app = create_app()
client = TestClient(app)

_ACCESS_TOKEN = create_access_token(subject="test-evidence")
_AUTH_HEADERS = {"Authorization": f"Bearer {_ACCESS_TOKEN}"}


def _make_submission(
    source_type: SourceType = SourceType.peer_reviewed,
    content_type: ContentType = ContentType.publication,
) -> RawKnowledgeSubmission:
    """Crée une soumission valide pour les tests."""
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=content_type,
        contenu={"title": "Test connaissance", "data": 42},
        source_candidate=SourceReference(
            type_source=source_type,
            auteur="IGN",
            date_publication="2024-01-15",
            reference="DOI:10.1234/test",
            version_source="1.0",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test_user",
    )


# --- Tests du wrapper ---


def should_return_version_when_engine_version_called():
    """engine_version doit retourner une version non vide."""
    version = engine_version()
    assert len(version) > 0


def should_detect_rust_availability():
    """is_rust_available doit retourner un booléen."""
    assert isinstance(is_rust_available(), bool)


def should_return_level_b_when_peer_reviewed_and_publication():
    """Peer-reviewed + publication doit donner niveau B."""
    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.B
    assert result.statut == KnowledgeStatus.accepte


def should_return_level_b_when_referentiel_officiel_and_referentiel():
    """Référentiel officiel + référentiel doit donner niveau B (plafond B).

    Le niveau A exige la convergence multi-sources (≥ 3) selon
    EVIDENCE_FRAMEWORK.md section 3.1 — non attribuable par une
    évaluation source unique.
    """
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.B
    assert result.statut == KnowledgeStatus.accepte


def should_return_level_c_when_peer_reviewed_and_expert():
    """Peer-reviewed + expert doit donner niveau C."""
    sub = _make_submission(SourceType.peer_reviewed, ContentType.expert)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.C
    assert result.statut == KnowledgeStatus.accepte


def should_return_level_d_when_expert_identifie_and_expert():
    """Expert identifié + expert doit donner niveau D."""
    sub = _make_submission(SourceType.expert_identifie, ContentType.expert)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.D
    assert result.statut == KnowledgeStatus.quarantine


def should_return_level_f_when_observation_terrain():
    """Observation terrain doit donner niveau F (plafond F).

    Observation isolée, non recoupée — EVIDENCE_FRAMEWORK.md section 3.1.
    """
    sub = _make_submission(SourceType.observation_terrain, ContentType.observation)
    result = evaluate(sub)
    assert result.evidence_level == EvidenceLevel.F
    assert result.statut == KnowledgeStatus.refuse


def should_generate_connaissance_id_when_evaluated():
    """L'évaluation doit générer un UUID pour connaissance_id."""
    sub = _make_submission()
    result = evaluate(sub)
    assert result.connaissance_id is not None


def should_set_version_to_1_when_newly_evaluated():
    """La version doit être 1 pour une nouvelle connaissance."""
    sub = _make_submission()
    result = evaluate(sub)
    assert result.version == 1


def should_preserve_contenu_when_evaluated():
    """Le contenu doit être préservé dans la connaissance qualifiée."""
    sub = _make_submission()
    result = evaluate(sub)
    assert result.contenu_normalise["data"] == 42


def should_preserve_source_when_evaluated():
    """La source doit être préservée dans la connaissance qualifiée."""
    sub = _make_submission()
    result = evaluate(sub)
    assert result.source.reference == "DOI:10.1234/test"


# --- Tests de l'API ---


def should_return_200_when_evidence_status_requested():
    """GET /api/v1/evidence/status doit retourner 200."""
    response = client.get("/api/v1/evidence/status")
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "evidence"


def should_return_200_when_evidence_version_requested():
    """GET /api/v1/evidence/version doit retourner la version."""
    response = client.get("/api/v1/evidence/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "backend" in data


def should_return_200_when_valid_submission_evaluated():
    """POST /api/v1/evidence/evaluate doit retourner 200 avec une connaissance qualifiée."""
    sub = _make_submission()
    response = client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evidence_level"] == "B"
    assert data["statut"] == "accepte"
    assert data["version"] == 1


def should_return_422_when_author_missing():
    """POST /api/v1/evidence/evaluate doit retourner 422 si auteur manquant."""
    sub = _make_submission()
    payload = sub.model_dump(mode="json")
    payload["source_candidate"]["auteur"] = ""
    response = client.post(
        "/api/v1/evidence/evaluate",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 422


def should_return_422_when_reference_missing():
    """POST /api/v1/evidence/evaluate doit retourner 422 si référence manquante."""
    sub = _make_submission()
    payload = sub.model_dump(mode="json")
    payload["source_candidate"]["reference"] = ""
    response = client.post(
        "/api/v1/evidence/evaluate",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 422


def should_return_422_when_invalid_source_type():
    """POST /api/v1/evidence/evaluate doit retourner 422 si type_source invalide."""
    sub = _make_submission()
    payload = sub.model_dump(mode="json")
    payload["source_candidate"]["type_source"] = "invalid_type"
    response = client.post(
        "/api/v1/evidence/evaluate",
        json=payload,
        headers=_AUTH_HEADERS,
    )
    assert response.status_code == 422


def should_return_level_b_via_api_when_referentiel():
    """L'API doit retourner niveau B pour référentiel officiel + référentiel.

    Plafond B — le niveau A exige la convergence multi-sources (≥ 3).
    """
    sub = _make_submission(SourceType.referentiel_officiel, ContentType.referentiel)
    response = client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    data = response.json()
    assert data["evidence_level"] == "B"
    assert data["statut"] == "accepte"


def should_return_quarantine_via_api_when_expert():
    """L'API doit retourner quarantine pour expert identifié (niveau D)."""
    sub = _make_submission(SourceType.expert_identifie, ContentType.expert)
    response = client.post(
        "/api/v1/evidence/evaluate",
        json=sub.model_dump(mode="json"),
        headers=_AUTH_HEADERS,
    )
    data = response.json()
    assert data["evidence_level"] == "D"
    assert data["statut"] == "quarantine"


# --- Tests du fallback Python ---


def should_use_python_fallback_when_rust_unavailable():
    """Le fallback Python doit fonctionner quand Rust n'est pas disponible."""
    from unittest.mock import patch

    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(wrapper_module, "_RUST_AVAILABLE", False):
        sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
        result = wrapper_module.evaluate(sub)
        assert result.evidence_level == EvidenceLevel.B
        assert result.statut == KnowledgeStatus.accepte


def should_return_python_fallback_version_when_rust_unavailable():
    """engine_version doit retourner la version fallback quand Rust indisponible."""
    from unittest.mock import patch

    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(wrapper_module, "_RUST_AVAILABLE", False):
        version = wrapper_module.engine_version()
        assert "fallback" in version


def should_return_level_f_via_fallback_when_unknown_combination():
    """Le fallback doit retourner F pour une combinaison inconnue."""
    from unittest.mock import patch

    import gsie_api.engines.evidence.wrapper as wrapper_module

    # Créer une soumission avec une combinaison qui n'est pas dans la matrice
    # En mockant le dictionnaire pour simuler un cas non couvert
    with (
        patch.object(wrapper_module, "_RUST_AVAILABLE", False),
        patch.dict(wrapper_module._DECISION_MATRIX, {}, clear=True),
    ):
        sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
        result = wrapper_module.evaluate(sub)
        assert result.evidence_level == EvidenceLevel.F
        assert result.statut == KnowledgeStatus.refuse


def should_fallback_to_python_when_rust_raises_exception():
    """Le wrapper doit fallback vers Python si l'appel Rust lève une exception.

    Panic recovery (P0 résilience) — si le moteur Rust crash ou lève
    une erreur de sérialisation, l'API ne doit pas crasher mais
    utiliser le fallback Python.
    """
    import gsie_api.engines.evidence.wrapper as wrapper_module

    if not wrapper_module._RUST_AVAILABLE:
        from pytest import skip

        skip("Rust Evidence Engine not available — fallback test requires Rust")

    from unittest.mock import patch

    # Simuler une exception lors de l'appel Rust
    with (
        patch.object(wrapper_module, "_RUST_AVAILABLE", True),
        patch.object(
            wrapper_module._rust_engine.EvidenceEngine,
            "evaluate_json",
            side_effect=RuntimeError("Rust panic simulated"),
        ),
    ):
        sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
        result = wrapper_module.evaluate(sub)
        # Le fallback Python doit produire le même résultat
        assert result.evidence_level == EvidenceLevel.B
        assert result.statut == KnowledgeStatus.accepte


def should_include_trace_id_in_404_error():
    """Le handler 404 doit inclure le trace_id dans la réponse d'erreur (RFC 7807)."""
    response = client.get("/nonexistent", headers={"X-Trace-Id": "test-trace-123"})
    assert response.status_code == 404
    data = response.json()
    # RFC 7807 Problem Details
    assert data["error_code"] == "NOT_FOUND"
    assert data["trace_id"] == "test-trace-123"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert "instance" in data


# --- Tests detect_conflicts ---


def should_detect_conflict_when_same_reference_different_type():
    """detect_conflicts doit détecter un conflit : même référence, type différent."""
    from gsie_api.engines.evidence.wrapper import detect_conflicts

    candidate = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Smith",
        reference="DOI:10.1234/test",
    )
    existing = [
        SourceReference(
            type_source=SourceType.expert_identifie,
            auteur="Jones",
            reference="doi:10.1234/test",  # même DOI, casse différente
        )
    ]
    conflits = detect_conflicts(candidate, existing)
    assert len(conflits) == 1
    assert "divergent" in conflits[0].description.lower()


def should_not_detect_conflict_when_same_reference_same_type():
    """detect_conflicts ne doit pas détecter de conflit si même type."""
    from gsie_api.engines.evidence.wrapper import detect_conflicts

    candidate = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Smith",
        reference="DOI:10.1234/test",
    )
    existing = [
        SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Jones",
            reference="DOI:10.1234/test",
        )
    ]
    conflits = detect_conflicts(candidate, existing)
    assert len(conflits) == 0


def should_detect_conflict_when_same_author_date_different_reference():
    """detect_conflicts doit détecter : même auteur + date, références différentes."""
    from gsie_api.engines.evidence.wrapper import detect_conflicts

    candidate = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Smith",
        date_publication="2024-01-01",
        reference="DOI:10.1234/a",
    )
    existing = [
        SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="smith",  # casse différente
            date_publication="2024-01-01",
            reference="DOI:10.1234/b",
        )
    ]
    conflits = detect_conflicts(candidate, existing)
    assert len(conflits) == 1
    assert "attribution" in conflits[0].description.lower()


def should_return_empty_conflicts_when_no_existing():
    """detect_conflicts doit retourner une liste vide sans sources existantes."""
    from gsie_api.engines.evidence.wrapper import detect_conflicts

    candidate = SourceReference(
        type_source=SourceType.peer_reviewed,
        auteur="Smith",
        reference="DOI:10.1234/test",
    )
    conflits = detect_conflicts(candidate, [])
    assert len(conflits) == 0


# --- Tests versionnement ---


def should_set_version_to_2_when_parent_version_is_1():
    """evaluate_with_context doit incrémenter la version avec un parent."""
    from gsie_api.engines.evidence.wrapper import evaluate_with_context

    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = evaluate_with_context(sub, parent_version=1)
    assert result.version == 2


def should_set_version_to_1_when_no_parent():
    """evaluate_with_context doit mettre version=1 sans parent."""
    from gsie_api.engines.evidence.wrapper import evaluate_with_context

    sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
    result = evaluate_with_context(sub)
    assert result.version == 1


def should_return_refuse_when_conflict_detected():
    """evaluate_with_context doit retourner refuse quand un conflit est détecté."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(
        wrapper_module._settings,
        "evidence_experimental_conflicts_enabled",
        True,
    ):
        sub = _make_submission(SourceType.peer_reviewed, ContentType.publication)
        sub.source_candidate.reference = "DOI:10.1234/conflict"
        existing = [
            SourceReference(
                type_source=SourceType.expert_identifie,
                auteur="Other",
                reference="DOI:10.1234/conflict",
            )
        ]
        result = wrapper_module.evaluate_with_context(sub, existing_sources=existing)
        assert result.statut == KnowledgeStatus.refuse
        assert len(result.conflits) > 0


# --- Tests /metrics ---


def should_return_200_when_metrics_requested():
    """GET /metrics doit retourner les métriques Prometheus."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus expose du texte, pas du JSON
    assert "http_request" in response.text or "python_info" in response.text
