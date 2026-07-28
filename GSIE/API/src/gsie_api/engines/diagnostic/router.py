"""Engine Diagnostic — synthèse explicable de l'état d'une station.

Responsabilité (`DIAGNOSTIC_ENGINE.md` §1) : assembler les conclusions
qualifiées du Reasoning Engine en un diagnostic stationnel structuré
(contraintes, atouts, risques, contradictions), sans jamais inventer de
classement ni déduire un état global par un score implicite. Ne produit
aucune recommandation — séparation des responsabilités (§6).

Un diagnostic sort toujours à l'état `brouillon` : seul un humain le
valide (`GSIE-CON-001`).

Endpoints :
- GET  /diagnostic/status       — statut du moteur
- GET  /diagnostic/version      — version et backend
- POST /diagnostic/diagnostiquer — produit un diagnostic explicable
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineWriteUser
from gsie_api.engines.diagnostic.engine import DiagnosticEngine, DiagnosticEngineError
from gsie_api.engines.diagnostic.schemas import Diagnostic, DiagnosticRequest
from gsie_api.infrastructure.database import get_db as get_db_session
from gsie_api.shared.schemas import EngineStatusResponse, EngineVersionResponse

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Exemple réaliste — prolonge l'exemple du Reasoning Engine (même station,
# même source) afin que les deux illustrent la chaîne Reasoning → Diagnostic.
# La source est celle déjà retenue dans l'exemple Reasoning validé
# (GSIE-PROMPT-0017) : aucune affirmation scientifique nouvelle n'est
# introduite ici, conformément à GSIE-CON-002 et ADR-009.
_SOURCE_RAMEAU: dict[str, object] = {
    "type_source": "peer_reviewed",
    "auteur": "Rameau et al. (2008)",
    "reference": "Flore forestière française, tome 1, IDF",
    "date_publication": "2008",
}

_EXEMPLE_REQUETE: dict[str, object] = {
    "requete_id": "550e8400-e29b-41d4-a716-446655440000",
    "station_id": "660e8400-e29b-41d4-a716-446655440001",
    "type_diagnostic": "stationnel",
    "conclusions": [
        {
            "conclusion_id": "770e8400-e29b-41d4-a716-446655440002",
            "enonce": "Le pH de la station est dans la gamme du chêne sessile.",
            "niveau_confiance": 0.8,
            "methode_confiance": "fournie_par_regle",
            "evidence_level_plancher": "B",
            "chaine_inference": [
                {
                    "ordre": 1,
                    "regle_appliquee": "R_PH_CHENE_SESSILE",
                    "source_regle": _SOURCE_RAMEAU,
                    "premisses": ["pH <= 6.0"],
                    "conclusion_locale": ("Le pH de la station est dans la gamme du chêne sessile"),
                    "evidence_level": "B",
                },
            ],
            "sources_utilisees": [_SOURCE_RAMEAU],
            "connaissances_utilisees": ["990e8400-e29b-41d4-a716-446655440004"],
            "moteurs_solicites": ["PEDOLOGY"],
        },
    ],
    "qualifications": [
        {
            "conclusion_id": "770e8400-e29b-41d4-a716-446655440002",
            "role": "contrainte",
            "domaine_element": "pedologique",
        },
    ],
    "etat_global": {
        "etat": "vigueur_reduite",
        "justification": (
            "Vigueur réduite déclarée par l'observateur au vu de la contrainte "
            "pédologique relevée sur la station."
        ),
        "source": _SOURCE_RAMEAU,
        "evidence_level": "B",
    },
    "contradictions": [],
    "contexte": {
        "pedologie": {
            "source_moteur": "PEDOLOGY",
            "source": _SOURCE_RAMEAU,
            "evidence_level": "B",
            "valeurs": {"pH": 5.2},
        },
    },
}


@router.get(
    "/status",
    response_model=EngineStatusResponse,
    summary="Statut du moteur Diagnostic",
    description=(
        "Retourne l'état courant du moteur Diagnostic : nom, statut "
        "(active/degraded/not_implemented), semaine d'implémentation prévue "
        "et langage. Aucune authentification requise — information publique."
    ),
)
async def diagnostic_status(request: Request) -> EngineStatusResponse:
    """Statut du moteur Diagnostic."""
    # Ordre de développement 11 — DIAGNOSTIC_ENGINE.md, en-tête du document.
    return EngineStatusResponse(
        engine="diagnostic",
        status="active",
        planned_week=11,
        language="python",
    )


@router.get(
    "/version",
    response_model=EngineVersionResponse,
    summary="Version du moteur Diagnostic",
    description=(
        "Retourne la version du moteur Diagnostic et le backend utilisé "
        "(postgresql). Aucune authentification requise — information publique."
    ),
)
async def diagnostic_version(request: Request) -> EngineVersionResponse:
    """Retourne la version du moteur et le backend utilisé."""
    return EngineVersionResponse(
        version=DiagnosticEngine.version(),
        backend="postgresql",
    )


@router.post(
    "/diagnostiquer",
    response_model=Diagnostic,
    status_code=status.HTTP_200_OK,
    summary="Produire un diagnostic explicable",
    description=(
        "Assemble les conclusions qualifiées du Reasoning Engine en un "
        "diagnostic stationnel : contraintes, atouts, risques et "
        "contradictions entre domaines. Chaque élément conserve la chaîne "
        "d'inférence et les sources de la conclusion dont il provient "
        "(GSIE-CON-002, GSIE-CON-004).\n\n"
        "Le moteur ne classe rien de lui-même : le rôle et le domaine de "
        "chaque conclusion, ainsi que l'état global, sont déclarés et "
        "sourcés par l'appelant. Déduire un état global d'un ensemble de "
        "contraintes exigerait une fonction de score que le moteur ne "
        "possède pas et ne doit pas inventer.\n\n"
        "Le diagnostic est toujours retourné à l'état `brouillon` : sa "
        "validation relève exclusivement d'un humain (GSIE-CON-001)."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": (
                "La requête est cohérente au sens du schéma mais "
                "indiagnosticable : chaîne d'inférence vide, contradiction "
                "inconstructible (domaines identiques ou non comparables), "
                "ou aucun élément produit. Le détail ne divulgue ni chemin "
                "de fichier, ni trace, ni structure interne."
            ),
            "content": {
                "application/json": {
                    "example": {"detail": "Aucun élément de diagnostic produit"},
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": (
                "La requête est invalide : champ manquant, type incorrect, "
                "conclusion non qualifiée, qualification orpheline, ou "
                "contradiction visant une conclusion absente."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "etat_global"],
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
@_limiter.limit("30/minute")
async def diagnostic_diagnostiquer(
    request_body: Annotated[
        DiagnosticRequest,
        Body(
            openapi_examples={
                "station_acide": {
                    "summary": "Station acide — contrainte pédologique",
                    "description": (
                        "Prolonge l'exemple du Reasoning Engine : la conclusion "
                        "sur le pH est qualifiée en contrainte pédologique, et "
                        "l'état global est déclaré avec sa source."
                    ),
                    "value": _EXEMPLE_REQUETE,
                },
            }
        ),
    ],
    request: Request,
    response: Response,
    session: DbSession,
    _user: EngineWriteUser,
) -> Diagnostic:
    """Produit un diagnostic à partir de conclusions qualifiées.

    Raises:
        400: Si la requête est indiagnosticable (voir `responses`).
    """
    try:
        # L'horloge est fournie par la couche API, jamais lue dans le moteur :
        # c'est ce qui rend le diagnostic reproductible et testable
        # (`CODE_QUALITY_STANDARD.md` §3.3).
        return await DiagnosticEngine(session).diagnostiquer(
            request_body,
            date_diagnostic=datetime.now(UTC),
        )
    except DiagnosticEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
