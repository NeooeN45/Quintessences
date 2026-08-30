"""Orchestration — un appel HTTP pour toute la chaîne GSIE.

    Reasoning → Diagnostic → Recommendation → Validation

Aucun endpoint ne couvrait la chaîne : `pipeline.py` n'orchestre
qu'Evidence → Knowledge et n'est exposé nulle part. Un client — l'application
GeoSylva — devait donc enchaîner quatre appels et reproduire de son côté les
conversions de `validation_pipeline.py`. Chaque passage de main était un point
de rupture que rien ne surveillait, et la logique de couture se serait
dupliquée dans chaque client.

Endpoints :
- GET  /orchestration/status  — statut
- GET  /orchestration/version — version
- POST /orchestration/analyse — déroule la chaîne et retourne chaque étape

La réponse porte les **quatre** sorties, pas seulement la dernière : un
forestier à qui l'on ne présenterait que la recommandation ne pourrait voir ni
le raisonnement qui la fonde, ni le diagnostic qu'elle invoque, ni ce que la
validation a contrôlé (`GSIE-CON-004`).
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineReadUser, EngineWriteUser
from gsie_api.engines.diagnostic.engine import DiagnosticEngineError
from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.engines.orchestration.hydration import (
    HydratationVideError,
    ResultatHydratation,
    StationContexteHydrator,
    StationIntrouvableError,
)
from gsie_api.engines.orchestration.idempotency import AnalyseIdempotencyConflictError
from gsie_api.engines.orchestration.preparation import (
    EtatGlobalNonSourceError,
    QualificationRegleManquanteError,
    ReglesQualifieesAbsentesError,
    ResultatPreparation,
    StationPreparationService,
    VersionRegleManquanteError,
)
from gsie_api.engines.orchestration.schemas import AnalyseComplete, AnalyseRequest
from gsie_api.engines.orchestration.service import (
    AnalyseImpossibleError,
    OrchestrationEngine,
)
from gsie_api.engines.reasoning.engine import ReasoningEngineError
from gsie_api.engines.recommendation.engine import RecommendationEngineError
from gsie_api.engines.validation_pipeline import PipelineError
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/orchestration", tags=["orchestration"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/status", response_model=EngineStatusResponse)
async def orchestration_status(request: Request) -> EngineStatusResponse:
    """Statut de l'orchestration."""
    return EngineStatusResponse(
        engine="orchestration",
        status="active",
        # Semaine du pipeline Evidence -> Knowledge, dont ce module reprend
        # le precedent : brancher les moteurs sans logique metier ajoutee.
        planned_week=4,
        language="python",
    )


@router.get("/version", response_model=EngineVersionResponse)
async def orchestration_version(request: Request) -> EngineVersionResponse:
    """Version de l'orchestration."""
    return EngineVersionResponse(
        version=OrchestrationEngine.version(),
        backend="python",
    )


@router.post(
    "/analyse",
    response_model=AnalyseComplete,
    status_code=status.HTTP_200_OK,
    summary="Dérouler la chaîne complète et retourner chaque étape",
    description=(
        "Enchaîne Reasoning → Diagnostic → Recommendation → Validation sur une "
        "session unique. Les qualifications de conclusions et l'état global "
        "sont déclarés par l'appelant : aucun moteur ne les devine "
        "(GSIE-CON-001, ADR-009). Le rejeu avec le même `requete_id` est "
        "idempotent et retourne la preuve existante."
    ),
)
@_limiter.limit("20/minute")
async def orchestration_analyse(
    request_body: AnalyseRequest,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> AnalyseComplete:
    """Déroule la chaîne complète.

    L'horloge est lue **ici**, une seule fois, et transmise aux moteurs qui
    l'exigent en entrée : le raisonnement et le diagnostic doivent partager le
    même instant, sinon deux étapes du même appel portent deux dates.

    Raises:
        400: requête incomplète — conclusion sans qualification déclarée,
            aucune règle applicable, ou refus d'un moteur.
    """
    if idempotency_key is not None and idempotency_key != str(request_body.requete_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key doit être égal à requete_id",
        )
    response.headers["Idempotency-Key"] = str(request_body.requete_id)
    try:
        return await OrchestrationEngine(session).analyser_idempotente(
            request_body, datetime.now(UTC)
        )
    except AnalyseIdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except StationIntrouvableError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except HydratationVideError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (
        AnalyseImpossibleError,
        ReasoningEngineError,
        DiagnosticEngineError,
        RecommendationEngineError,
        PipelineError,
    ) as exc:
        # Le message des moteurs est repris tel quel : il nomme ce qui manque,
        # et c'est ce dont l'appelant a besoin pour corriger. Un « requête
        # invalide » generique l'obligerait a deviner lequel des quatre moteurs
        # a refuse, et pourquoi.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/stations/{station_id}/contexte",
    response_model=ResultatHydratation,
    summary="Prévisualiser le contexte hydraté d'une station",
    description=(
        "Assemble le StationContexte depuis `station_id` (DEC-000072) sans "
        "exécuter la chaîne : Place d'abord, soumission terrain acceptée en "
        "repli tracé, provenance complète exigée pour chaque bloc. Le rapport "
        "nomme chaque bloc construit, chaque manque et chaque niveau de "
        "preuve déclaré utilisé."
    ),
)
@_limiter.limit("30/minute")
async def previsualiser_contexte_station(
    station_id: UUID,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineReadUser,
    niveau_geographie: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_climat: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_pedologie: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_botanique: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_peuplement: Annotated[EvidenceLevel | None, Query()] = None,
) -> ResultatHydratation:
    """Prévisualise l'hydratation — debug serveur et futur écran GeoSylva."""
    niveaux = {
        nom[7:]: niveau
        for nom, niveau in (
            ("niveau_geographie", niveau_geographie),
            ("niveau_climat", niveau_climat),
            ("niveau_pedologie", niveau_pedologie),
            ("niveau_botanique", niveau_botanique),
            ("niveau_peuplement", niveau_peuplement),
        )
        if niveau is not None
    }
    try:
        return await StationContexteHydrator(session).hydrate(station_id, niveaux_declares=niveaux)
    except StationIntrouvableError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except HydratationVideError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/stations/{station_id}/preparation",
    response_model=ResultatPreparation,
    summary="Préparer les entrées qualifiées d'une analyse stationnelle",
    description=(
        "Hydrate la station, sélectionne les règles accepted applicables et "
        "récupère l'état global d'un FieldIntake accepted. N'exécute aucun moteur "
        "et refuse toute absence de provenance ou de qualification."
    ),
)
@_limiter.limit("20/minute")
async def preparer_analyse_station(
    station_id: UUID,
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineReadUser,
    niveau_geographie: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_climat: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_pedologie: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_botanique: Annotated[EvidenceLevel | None, Query()] = None,
    niveau_peuplement: Annotated[EvidenceLevel | None, Query()] = None,
) -> ResultatPreparation:
    """Prépare et expose les entrées, sans lancer Reasoning ou Diagnostic."""
    niveaux = {
        nom[7:]: niveau
        for nom, niveau in (
            ("niveau_geographie", niveau_geographie),
            ("niveau_climat", niveau_climat),
            ("niveau_pedologie", niveau_pedologie),
            ("niveau_botanique", niveau_botanique),
            ("niveau_peuplement", niveau_peuplement),
        )
        if niveau is not None
    }
    try:
        return await StationPreparationService(session).prepare(
            station_id, niveaux_declares=niveaux
        )
    except StationIntrouvableError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except HydratationVideError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (
        ReglesQualifieesAbsentesError,
        QualificationRegleManquanteError,
        EtatGlobalNonSourceError,
        VersionRegleManquanteError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
