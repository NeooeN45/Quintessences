"""Engine Validation — contrôle final avant présentation à l'utilisateur.

Responsabilité : vérifier la cohérence, la conformité constitutionnelle
et la complétude des diagnostics et recommandations avant leur
présentation, en bloquant toute sortie non conforme
(VALIDATION_ENGINE.md §1). Le moteur ne produit pas de contenu — il
valide et filtre (§6).

Endpoints :
- GET  /validation/status   — statut du moteur
- GET  /validation/version   — version et backend
- POST /validation/validate  — valide une sortie (diagnostic, recommandation ou ensemble)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.validation.engine import ValidationEngine, ValidationEngineError
from gsie_api.engines.validation.schemas import ValidationRequest, ValidationResult
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/validation", tags=["validation"])

_validate_limiter = Limiter(key_func=get_remote_address)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def validation_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Validation."""
    return EngineStatusResponse(
        engine="validation",
        status="active",
        planned_week=13,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Validation",
)
async def validation_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=ValidationEngine.version(),
        backend="python",
    )


@router.post(
    "/validate",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Valider une sortie avant présentation à l'utilisateur",
    description=(
        "Applique les contrôles de cohérence, conformité constitutionnelle "
        "et complétude à une sortie (diagnostic, recommandation ou ensemble "
        "complet). Bloque toute sortie non conforme avec cause de blocage "
        "traçable (GSIE-CON-001, CON-002, CON-004, CON-005)."
    ),
)
@_validate_limiter.limit("60/minute")
async def validation_validate(
    request_body: ValidationRequest,
    request: Request,
    session: DbSession,
    _user: EngineWriteUser,
) -> ValidationResult:
    """Valide une sortie.

    Le blocage n'est pas une erreur HTTP : un `statut=bloque` est
    retourné en 200 avec les causes de blocage. Une erreur 400
    n'est levée que si la requête est malformée au-delà du schéma
    Pydantic (par exemple une incohérence interne).
    """
    try:
        return await ValidationEngine().validate(request_body)
    except ValidationEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
