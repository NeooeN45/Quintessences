"""Engine Reasoning — inférence explicable sur connaissances qualifiées.

Responsabilité (REASONING_ENGINE.md §1) : appliquer des règles d'inférence
explicites et auditées sur les connaissances et corrélations qualifiées
pour produire des conclusions expliquées et traçables, sans jamais inventer
de règle (GSIE-CON-002). Ne produit ni diagnostic ni recommandation —
séparation des responsabilités (§6).

Endpoints :
- GET  /reasoning/status   — statut du moteur
- GET  /reasoning/version  — version et backend
- POST /reasoning/infer    — produit une inférence explicable

Note : engine.py est implémenté par l'agent R2 en parallèle. L'import
ci-dessous suit le même pattern que le Correlation Engine
(``CorrelationEngine`` + ``CorrelationEngineError``). Le commentaire
``type: ignore`` sera à retirer dès que engine.py sera disponible.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.rbac import EngineWriteUser
from gsie_api.engines.reasoning.engine import ReasoningEngine, ReasoningEngineError
from gsie_api.engines.reasoning.schemas import InferenceResult, ReasoningRequest
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/reasoning", tags=["reasoning"])

_infer_limiter = Limiter(key_func=get_remote_address)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Exemple réaliste de requête d'inférence — station forestière acide
# avec question d'adaptation d'essence. Les valeurs pédologiques sont
# typiques d'une station à chêne sessile (Rameau et al., 2008).
_EXEMPLE_REQUETE: dict[str, object] = {
    "requete_id": "550e8400-e29b-41d4-a716-446655440000",
    "station_id": "660e8400-e29b-41d4-a716-446655440001",
    "contexte": {
        "pedologie": {
            "source_moteur": "PEDOLOGY",
            "source": {
                "type_source": "referentiel_officiel",
                "auteur": "INRAE (2008)",
                "date_publication": "2008",
                "reference": "Référentiel pédologique français, édition 2008",
            },
            "evidence_level": "B",
            "valeurs": {"pH": 5.2, "profondeur_cm": 80, "texture": "sablonneux"},
        },
        "climat": {
            "source_moteur": "CLIMATE",
            "source": {
                "type_source": "referentiel_officiel",
                "auteur": "Météo-France (2024)",
                "date_publication": "2024",
                "reference": "Normales climatiques 1991-2020, station 36083002",
            },
            "evidence_level": "B",
            "valeurs": {"precipitations_mm": 850, "temperature_moyenne": 11.2},
        },
    },
    "question": "Quelles essences sont adaptées à cette station ?",
    "profondeur_max": 5,
}

# Exemple réaliste de réponse — inférence avec une conclusion
_EXEMPLE_REPONSE: dict[str, object] = {
    "resultat_id": "770e8400-e29b-41d4-a716-446655440002",
    "requete_origine": "550e8400-e29b-41d4-a716-446655440000",
    "conclusions": [
        {
            "conclusion_id": "880e8400-e29b-41d4-a716-446655440003",
            "enonce": "Le chêne sessile est adapté à cette station",
            "niveau_confiance": 0.82,
            "methode_confiance": "fournie_par_regle",
            "evidence_level_plancher": "B",
            "chaine_inference": [
                {
                    "ordre": 1,
                    "regle_appliquee": (
                        "Le chêne sessile est adapté aux sols acides à "
                        "modérément acides (pH 4,5-6,0)"
                    ),
                    "source_regle": {
                        "type_source": "peer_reviewed",
                        "auteur": "Rameau et al. (2008)",
                        "date_publication": "2008",
                        "reference": "Flore forestière française, tome 1, IDF",
                    },
                    "regle_id": "990e8400-e29b-41d4-a716-446655440004",
                    "premisses": ["pH station = 5,2"],
                    "conclusion_locale": "Le pH de la station est dans la gamme du chêne sessile",
                    "evidence_level": "B",
                },
            ],
            "sources_utilisees": [
                {
                    "type_source": "peer_reviewed",
                    "auteur": "Rameau et al. (2008)",
                    "date_publication": "2008",
                    "reference": "Flore forestière française, tome 1, IDF",
                },
            ],
            "connaissances_utilisees": ["990e8400-e29b-41d4-a716-446655440004"],
            "moteurs_solicites": ["PEDOLOGY", "CLIMATE"],
        },
    ],
    "contradictions": [],
    "date_inference": "2026-07-25T12:00:00Z",
}


@router.get(
    "/status",
    response_model=EngineStatusResponse,
    summary="Statut du moteur Reasoning",
    description=(
        "Retourne l'état courant du moteur Reasoning : nom, statut "
        "(active/degraded/not_implemented), semaine d'implémentation prévue "
        "et langage. Aucune authentification requise — information publique."
    ),
)
async def reasoning_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Reasoning."""
    # Ordre de développement 10 — REASONING_ENGINE.md, en-tête du document.
    return EngineStatusResponse(
        engine="reasoning",
        status="active",
        planned_week=10,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Reasoning",
    description=(
        "Retourne la version du moteur Reasoning et le backend utilisé "
        "(postgresql). Aucune authentification requise — information publique."
    ),
)
async def reasoning_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=ReasoningEngine.version(),
        backend="postgresql",
    )


@router.post(
    "/infer",
    response_model=InferenceResult,
    status_code=status.HTTP_200_OK,
    summary="Produire une inférence explicable",
    description=(
        "Applique les règles d'inférence du Knowledge Engine sur le contexte "
        "stationnel fourni pour produire des conclusions expliquées et "
        "traçables. Chaque conclusion porte sa chaîne d'inférence complète, "
        "ses sources et son niveau de preuve (GSIE-CON-002, GSIE-CON-004). "
        "Le moteur n'invente aucune règle — il applique uniquement celles "
        "fournies par le Knowledge Engine. Lorsqu'aucune règle applicable "
        "n'existe, l'absence de conclusion est un résultat honnête."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": (
                "La requête contient une règle mal formée ou non applicable "
                "à ce contexte. Le détail du message ne divulgue ni chemin "
                "de fichier, ni trace, ni structure interne."
            ),
            "content": {
                "application/json": {
                    "example": {"detail": "Règle non applicable à ce contexte"},
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": (
                "La requête est invalide : champ manquant, type incorrect, "
                "ou contexte stationnel vide (au moins un bloc requis)."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "contexte"],
                                "msg": "Field required",
                                "type": "missing",
                            },
                        ],
                    },
                },
            },
        },
    },
)
@_infer_limiter.limit("30/minute")
async def reasoning_infer(
    request_body: Annotated[
        ReasoningRequest,
        Body(
            openapi_examples={
                "station_acide": {
                    "summary": "Station acide — adaptation du chêne sessile",
                    "description": (
                        "Station forestière au pH acide (5,2) avec question "
                        "d'adaptation d'essence. Le moteur applique les règles "
                        "autécologiques du Knowledge Engine."
                    ),
                    "value": _EXEMPLE_REQUETE,
                },
            }
        ),
    ],
    request: Request,
    session: DbSession,
    _user: EngineWriteUser,
) -> InferenceResult:
    """Produit une inférence à partir d'un contexte stationnel.

    Raises:
        400: Si une règle fournie est mal formée ou non applicable.
    """
    try:
        # L'horloge est fournie par la couche API, jamais lue dans le moteur :
        # c'est ce qui rend l'inférence reproductible et testable
        # (`CODE_QUALITY_STANDARD.md` §3.3).
        return await ReasoningEngine(session).infer(request_body, date_inference=datetime.now(UTC))
    except ReasoningEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
