"""Router Gamification — statistiques d'engagement du dashboard.

Endpoint :
- GET /gamification/stats — badges, objectifs et série de jours

Sécurité : auth JWT obligatoire (lecture seule).

Note : les données sont actuellement statiques. Le moteur Gamification
n'est pas un des 14 moteurs GSIE ; il sera alimenté progressivement
pendant la Phase 4 à mesure que les moteurs produisent des événements
d'engagement traçables.
"""

from typing import Any

from fastapi import APIRouter, Request, Response

from gsie_api.core.limiter import limiter as _limiter
from gsie_api.core.rbac import EngineReadUser
from gsie_api.gamification.schemas import GamificationStats

router = APIRouter(prefix="/gamification", tags=["gamification"])

# Données statiques — remplacées par une source réelle quand le
# suivi d'engagement sera implémenté (événements moteurs → badges).
_BADGES: list[dict[str, Any]] = [
    {
        "id": "first-diagnostic",
        "name": "Premier diagnostic",
        "description": "Générer un premier diagnostic forestier",
        "icon": "stethoscope",
        "unlocked": True,
    },
    {
        "id": "data-explorer",
        "name": "Explorateur de données",
        "description": "Consulter 10 ressources différentes",
        "icon": "compass",
        "unlocked": True,
    },
    {
        "id": "knowledge-curator",
        "name": "Curateur de connaissances",
        "description": "Ingérer 5 connaissances validées",
        "icon": "book",
        "unlocked": False,
    },
    {
        "id": "climate-watch",
        "name": "Veille climatique",
        "description": "Consulter la vigilance Météo-France 7 jours d'affilée",
        "icon": "cloud",
        "unlocked": False,
    },
]

_GOALS: list[dict[str, Any]] = [
    {
        "id": "diagnostics-month",
        "label": "Diagnostics ce mois",
        "current": 3,
        "target": 10,
        "unit": "diagnostics",
    },
    {
        "id": "resources-curated",
        "label": "Ressources curées",
        "current": 12,
        "target": 20,
        "unit": "ressources",
    },
    {
        "id": "knowledge-validated",
        "label": "Connaissances validées",
        "current": 25,
        "target": 50,
        "unit": "connaissances",
    },
]

_STREAK_DAYS = 4


@router.get(
    "/stats",
    response_model=GamificationStats,
    summary="Statistiques d'engagement (badges, objectifs, série)",
    description=(
        "Retourne les badges débloqués/verrouillés, les objectifs de "
        "progression et la série de jours d'activité. Données "
        "actuellement statiques — seront alimentées par les événements "
        "moteurs pendant la Phase 4."
    ),
)
@_limiter.limit("30/minute")
async def gamification_stats(
    request: Request,
    response: Response,
    _user: EngineReadUser,
) -> GamificationStats:
    """Statistiques d'engagement du dashboard."""
    return GamificationStats(
        badges=_BADGES,
        goals=_GOALS,
        streak=_STREAK_DAYS,
    )
