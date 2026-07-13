"""Engine Evidence — évaluation de la qualité scientifique (Rust + PyO3).

Responsabilité : évaluer la qualité scientifique d'une connaissance
et lui attribuer un niveau de preuve sourcé et traçable (A-F).

Cœur Rust (gsie_evidence crate) exposé via PyO3 (ADR-0002).
Fallback Python si le module Rust n'est pas compilé.

États de l'art (EVIDENCE_ENGINE.md) : GRADE, CEE Guidelines,
GRADE-CERQual, ASReview, Rayyan, claim verification (SciFact/FEVER).
"""

from fastapi import APIRouter, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from gsie_api.engines.evidence.schemas import (
    QualifiedKnowledge,
    RawKnowledgeSubmission,
)
from gsie_api.engines.evidence.wrapper import engine_version, evaluate, is_rust_available
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])

# Rate limiter spécifique pour les endpoints POST coûteux (flood protection)
_evaluate_limiter = Limiter(key_func=get_remote_address)


@router.get("/status", response_model=EngineStatusResponse)
async def evidence_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Evidence."""
    rust_available = is_rust_available()
    return EngineStatusResponse(
        engine="evidence",
        status="active" if rust_available else "degraded",
        planned_week=2,
        language="rust+pyo3" if rust_available else "python-fallback",
    )


@router.post(
    "/evaluate",
    response_model=QualifiedKnowledge,
    status_code=status.HTTP_200_OK,
    summary="Évaluer une soumission de connaissance",
    description=(
        "Évalue la qualité scientifique d'une soumission et attribue "
        "un niveau de preuve (A-F) selon la matrice source × contenu. "
        "Le cœur d'évaluation est en Rust (gsie_evidence crate) exposé "
        "via PyO3 (ADR-0002)."
    ),
)
@_evaluate_limiter.limit("30/minute")
async def evidence_evaluate(
    submission: RawKnowledgeSubmission,
    request: Request,
) -> QualifiedKnowledge:
    """Évalue une soumission de connaissance brute.

    Pipeline :
    1. Validation Pydantic (schéma RawKnowledgeSubmission)
    2. Évaluation Rust (matrice de décision A-F)
    3. Retour de la connaissance qualifiée

    Le niveau de preuve dépend du type de source et du type de contenu :
    - A : référentiel officiel + contenu référentiel (consensus)
    - B : peer-reviewed + publication (établi)
    - C : peer-reviewed + expert/observation (probable)
    - D : expert identifié (non publié)
    - E : observation terrain
    - F : incertain/contesté

    Le statut est déterminé par le niveau :
    - A, B, C → accepte
    - D, E    → quarantine (validation humaine requise — CON-001)
    - F       → refuse
    """
    return evaluate(submission)


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Evidence",
)
async def evidence_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=engine_version(),
        backend="rust+pyo3" if is_rust_available() else "python-fallback",
    )
