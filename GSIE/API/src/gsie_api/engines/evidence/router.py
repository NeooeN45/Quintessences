"""Engine Evidence — placeholder (implémentation semaine 2, Rust + pyo3).

Responsabilité : évaluer la qualité scientifique d'une connaissance
et lui attribuer un niveau de preuve sourcé et traçable (A-F).

État de l'art (Fable 5) : GRADE, CEE Guidelines, GRADE-CERQual,
ASReview, Rayyan, claim verification (SciFact/FEVER), Retraction Watch.
"""

from fastapi import APIRouter, Request

from gsie_api.shared.schemas import EngineStatusResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/status", response_model=EngineStatusResponse)
async def evidence_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Evidence — non implémenté (semaine 2)."""
    return EngineStatusResponse(
        engine="evidence",
        status="not_implemented",
        planned_week=2,
        language="rust+pyo3",
    )
