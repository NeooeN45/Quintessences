"""Schémas Pydantic pour la feature Gamification.

Alignés sur le contrat du frontend (GamificationPanel.tsx) :
- Badge : id, name, description, icon, unlocked
- ProgressGoal : id, label, current, target, unit
- GamificationStats : badges, goals, streak
"""

from pydantic import BaseModel, Field


class Badge(BaseModel):
    """Badge d'engagement — débloqué ou verrouillé."""

    id: str = Field(..., description="Identifiant stable du badge")
    name: str = Field(..., description="Nom affiché")
    description: str = Field(..., description="Condition de déblocage")
    icon: str = Field(..., description="Nom de l'icône (clé frontend)")
    unlocked: bool = Field(..., description="Badge débloqué ou non")


class ProgressGoal(BaseModel):
    """Objectif de progression avec valeur courante et cible."""

    id: str = Field(..., description="Identifiant stable de l'objectif")
    label: str = Field(..., description="Libellé affiché")
    current: int = Field(..., ge=0, description="Valeur courante")
    target: int = Field(..., gt=0, description="Valeur cible")
    unit: str = Field(..., description="Unité affichée (ex. diagnostics)")


class GamificationStats(BaseModel):
    """Statistiques d'engagement complètes du dashboard."""

    badges: list[Badge] = Field(default_factory=list)
    goals: list[ProgressGoal] = Field(default_factory=list)
    streak: int = Field(0, ge=0, description="Série de jours d'activité")
