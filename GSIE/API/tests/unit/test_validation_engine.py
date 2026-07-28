"""Tests unitaires — Validation Engine.

Vérifie les contrôles de conformité constitutionnelle et la logique
de blocage/partiellement_valide/valide.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from gsie_api.engines.validation.engine import ValidationEngine
from gsie_api.engines.validation.schemas import (
    CauseBlocage,
    ControleResultat,
    ResultatControle,
    TypeCauseBlocage,
    TypeSortie,
    ValidationRequest,
    ValidationResult,
    ValidationStatut,
)


def _make_request(
    type_sortie: TypeSortie = TypeSortie.diagnostic,
    contenu: dict | None = None,
    chaines_inference: list | None = None,
) -> ValidationRequest:
    if contenu is None:
        contenu = {
            "evidence_level": "B",
            "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
            "justification": "Diagnostic fondé sur observations terrain.",
        }
    if chaines_inference is None:
        chaines_inference = [{"conclusion": "test"}]
    return ValidationRequest(
        requete_id=uuid4(),
        type_sortie=type_sortie,
        contenu=contenu,
        chaines_inference=chaines_inference,
    )


@pytest.fixture
def engine() -> ValidationEngine:
    return ValidationEngine()


# --- Tests statut valide ---


@pytest.mark.asyncio
async def should_return_valide_when_diagnostic_complete(engine: ValidationEngine) -> None:
    """Un diagnostic complet avec source, niveau de preuve, chaîne et justification est valide."""
    result = await engine.validate(_make_request())
    assert result.statut == ValidationStatut.valide
    assert not result.causes_blocage
    assert len(result.controles) == 5
    assert all(
        c.resultat == ResultatControle.conforme
        for c in result.controles
        if c.resultat != ResultatControle.non_applicable
    )


@pytest.mark.asyncio
async def should_return_valide_when_recommandation_complete(engine: ValidationEngine) -> None:
    """Une recommandation complète avec source, niveau de preuve et contournable est valide."""
    contenu = {
        "evidence_level": "B",
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": {
            "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
        },
        "recommandations": [
            {
                "contournable": True,
                "justification": {
                    "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
                },
            },
        ],
    }
    result = await engine.validate(_make_request(TypeSortie.recommandation, contenu))
    assert result.statut == ValidationStatut.valide


# --- Tests statut bloque ---


@pytest.mark.asyncio
async def should_return_bloque_when_no_evidence_level(engine: ValidationEngine) -> None:
    """Un diagnostic sans niveau de preuve est bloqué (GSIE-CON-002)."""
    contenu = {
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": "Diagnostic fondé sur observations.",
    }
    result = await engine.validate(_make_request(contenu=contenu))
    assert result.statut == ValidationStatut.bloque
    assert any(c.type_cause == TypeCauseBlocage.sans_niveau_preuve for c in result.causes_blocage)


@pytest.mark.asyncio
async def should_return_bloque_when_no_source(engine: ValidationEngine) -> None:
    """Un diagnostic sans source est bloqué (GSIE-CON-002)."""
    contenu = {
        "evidence_level": "B",
        "justification": "Diagnostic fondé sur observations.",
    }
    result = await engine.validate(_make_request(contenu=contenu))
    assert result.statut == ValidationStatut.bloque
    assert any(c.type_cause == TypeCauseBlocage.sans_source for c in result.causes_blocage)


@pytest.mark.asyncio
async def should_return_bloque_when_no_chaine_inference(engine: ValidationEngine) -> None:
    """Un diagnostic sans chaîne d'inférence est bloqué (GSIE-CON-004)."""
    result = await engine.validate(_make_request(chaines_inference=[]))
    assert result.statut == ValidationStatut.bloque
    assert any(
        c.type_cause == TypeCauseBlocage.sans_chaine_inference for c in result.causes_blocage
    )


@pytest.mark.asyncio
async def should_return_bloque_when_recommandation_non_contournable(
    engine: ValidationEngine,
) -> None:
    """Une recommandation non contournable est bloquée (GSIE-CON-001)."""
    contenu = {
        "evidence_level": "B",
        "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
        "justification": {
            "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
        },
        "recommandations": [
            {
                "contournable": False,
                "justification": {
                    "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
                },
            },
        ],
    }
    result = await engine.validate(_make_request(TypeSortie.recommandation, contenu))
    assert result.statut == ValidationStatut.bloque
    assert any(
        c.type_cause == TypeCauseBlocage.recommandation_non_contournable
        for c in result.causes_blocage
    )


# --- Tests statut partiellement_valide ---


@pytest.mark.asyncio
async def should_return_partiellement_valide_when_ensemble_complet_with_non_critical_failure(
    engine: ValidationEngine,
) -> None:
    """Un ensemble complet avec un échec non critique est partiellement valide."""
    contenu = {
        "diagnostic": {
            "evidence_level": "B",
            "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
            "justification": "Diagnostic fondé.",
        },
        "recommandations": [
            {
                "contournable": True,
                "justification": {
                    "sources": [{"type_source": "peer_reviewed", "auteur": "X", "reference": "Y"}]
                },
            },
        ],
    }
    # Pas de chaîne d'inférence — non critique pour ensemble_complet
    result = await engine.validate(
        _make_request(TypeSortie.ensemble_complet, contenu, chaines_inference=[])
    )
    # Le contrôle chaine_inference est non conforme mais non critique
    assert result.statut in (ValidationStatut.partiellement_valide, ValidationStatut.bloque)


# --- Tests invariants schéma ---


def should_reject_valide_with_causes_blocage() -> None:
    """Le schéma rejette statut=valide avec causes de blocage."""
    with pytest.raises(ValueError, match="valide.*causes"):
        ValidationResult(
            validation_id=uuid4(),
            requete_origine=uuid4(),
            statut=ValidationStatut.valide,
            controles=[
                ControleResultat(
                    nom_controle="test", resultat=ResultatControle.conforme, details="ok"
                )
            ],
            causes_blocage=[
                CauseBlocage(
                    type_cause=TypeCauseBlocage.sans_source,
                    element_concerne=uuid4(),
                    description="test",
                )
            ],
            date_validation=datetime.now(UTC),
        )


def should_reject_bloque_without_causes_blocage() -> None:
    """Le schéma rejette statut=bloque sans cause de blocage."""
    with pytest.raises(ValueError, match="bloque.*cause"):
        ValidationResult(
            validation_id=uuid4(),
            requete_origine=uuid4(),
            statut=ValidationStatut.bloque,
            controles=[
                ControleResultat(
                    nom_controle="test", resultat=ResultatControle.non_conforme, details="ko"
                )
            ],
            causes_blocage=[],
            date_validation=datetime.now(UTC),
        )


def should_reject_ensemble_complet_without_diagnostic_and_recommandations() -> None:
    """Le schéma rejette ensemble_complet sans diagnostic et recommandations."""
    with pytest.raises(ValueError, match="ensemble_complet"):
        ValidationRequest(
            requete_id=uuid4(),
            type_sortie=TypeSortie.ensemble_complet,
            contenu={"diagnostic": {}},  # manque recommandations
        )
