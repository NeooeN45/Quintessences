"""Correlation Engine — détection et quantification de corrélations statistiques.

Responsabilité (CORRELATION_ENGINE.md §1) :
- Détecter et quantifier des corrélations statistiques significatives
  entre variables issues de sources hétérogènes
- Sourcer et justifier statistiquement chaque corrélation (coefficient,
  p-valeur, taille d'échantillon) — CON-002
- Ne jamais présenter une corrélation comme une relation de causalité
  sans justification explicite (§6)
- Ne produire aucune recommandation — le moteur alimente le raisonnement,
  il ne décide pas (séparation des responsabilités, §6)

Périmètre v1 (voir docstring schemas.py) : les valeurs numériques sont
fournies directement dans la requête plutôt que récupérées auprès des
moteurs domaine (GIS, Climate, Pedology, Botanical, Forest Dynamics),
qui n'existent pas encore. Une seule paire de variables par requête
(pas de matrice N×N). Ces réductions sont volontaires et documentées,
pas un raccourci silencieux — le contrat de sortie (CorrelationResult)
respecte la forme du contrat cible (CORRELATION_ENGINE.md §5).

Persistance : chaque corrélation calculée est enregistrée comme
`resource(type=correlation)` + `CorrelationModel` (schéma v6.2), pour
être interrogeable plus tard par Reasoning, Diagnostic et Learning
(§3 — sorties du moteur). Les champs descriptifs sans colonne dédiée
(noms de variables, domaine, domaine_validite, source, evidence_level)
sont conservés dans `resource.metadata_json`, même convention que
Knowledge Engine.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from scipy import stats as scipy_stats
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.correlation.schemas import (
    CorrelationComputeRequest,
    CorrelationResult,
    TypeRelation,
)
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.enums import CorrelationMethod, CorrelationStrength
from gsie_api.infrastructure.models.reasoning import CorrelationModel

logger = get_logger("gsie_api.correlation.engine")

# Seuils de force de corrélation — Evans (1996), échelle usuelle en
# biostatistique pour |r| (repris tel quel pour |rho|/|tau| — pas de
# consensus séparé publié pour ces coefficients de rang).
_STRENGTH_THRESHOLDS: list[tuple[float, CorrelationStrength]] = [
    (0.80, CorrelationStrength.very_strong),
    (0.60, CorrelationStrength.strong),
    (0.40, CorrelationStrength.moderate),
    (0.20, CorrelationStrength.weak),
    (0.0, CorrelationStrength.negligible),
]

_METHOD_FUNCS = {
    CorrelationMethod.pearson: scipy_stats.pearsonr,
    CorrelationMethod.spearman: scipy_stats.spearmanr,
    CorrelationMethod.kendall: scipy_stats.kendalltau,
}


class CorrelationEngineError(Exception):
    """Erreur de base du Correlation Engine."""


class CorrelationEngine:
    """Moteur de calcul et de persistance des corrélations.

    Une instance est créée par requête HTTP avec la session DB de la
    requête (même schéma que KnowledgeEngine/ResourceService).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def version() -> str:
        """Version du moteur."""
        return "0.1.0"

    async def compute(self, request: CorrelationComputeRequest) -> CorrelationResult:
        """Calcule une corrélation entre deux variables et la persiste.

        Raises:
            CorrelationEngineError: si la méthode demandée n'est pas
                supportée (seules pearson/spearman/kendall calculent
                une p-valeur exploitable — les autres valeurs de
                CorrelationMethod, ex. « expert », « literature »,
                désignent des corrélations non recalculables ici).
        """
        method_func = _METHOD_FUNCS.get(request.methode)
        if method_func is None:
            raise CorrelationEngineError(
                f"Méthode {request.methode.value} non calculable par ce moteur "
                f"— méthodes supportées : {[m.value for m in _METHOD_FUNCS]}"
            )

        stat_result = method_func(request.variable_a.valeurs, request.variable_b.valeurs)
        coefficient = float(stat_result.statistic)
        p_valeur = float(stat_result.pvalue)

        if p_valeur >= request.seuil_significativite:
            type_relation = TypeRelation.non_significative
        else:
            type_relation = TypeRelation.positive if coefficient > 0 else TypeRelation.negative

        strength = self._classify_strength(abs(coefficient))
        confidence = max(0.0, min(1.0, 1.0 - p_valeur))
        n_observations = len(request.variable_a.valeurs)
        now = datetime.now(UTC)
        correlation_id = uuid4()

        variable_a_label = self._format_variable(
            request.variable_a.variable, request.variable_a.unite
        )
        variable_b_label = self._format_variable(
            request.variable_b.variable, request.variable_b.unite
        )

        metadata: dict[str, Any] = {
            "domaine": request.domaine.value,
            "variable_a": variable_a_label,
            "variable_b": variable_b_label,
            "source_moteur_a": request.variable_a.source_moteur.value,
            "source_moteur_b": request.variable_b.source_moteur.value,
            "n_observations": n_observations,
            "domaine_validite": request.domaine_validite,
            "source": request.source.model_dump(mode="json"),
            "evidence_level": request.evidence_level.value,
            "type_relation": type_relation.value,
        }

        self._session.add(
            ResourceModel(
                id=correlation_id,
                type="correlation",
                gsie_id=f"gsie:correlation:{correlation_id}",
                metadata_json=metadata,
            )
        )
        # Flush avant la table satellite qui référence resource.id en FK —
        # même contrainte que KnowledgeEngine (voir sa docstring).
        await self._session.flush()

        self._session.add(
            CorrelationModel(
                id=correlation_id,
                method=request.methode,
                coefficient=coefficient,
                strength=strength,
                confidence=confidence,
                p_value=p_valeur,
            )
        )
        await self._session.flush()

        logger.info(
            "correlation_computed",
            correlation_id=str(correlation_id),
            methode=request.methode.value,
            coefficient=coefficient,
            p_valeur=p_valeur,
            type_relation=type_relation.value,
            n_observations=n_observations,
        )

        return CorrelationResult(
            correlation_id=correlation_id,
            requete_origine=request.requete_id,
            variable_a=variable_a_label,
            variable_b=variable_b_label,
            methode=request.methode,
            coefficient=coefficient,
            p_valeur=p_valeur,
            type_relation=type_relation,
            strength=strength,
            n_observations=n_observations,
            domaine_validite=request.domaine_validite,
            source=request.source,
            evidence_level=request.evidence_level,
            confidence=confidence,
            date_calcul=now,
        )

    async def stats(self) -> dict[str, int]:
        """Retourne les statistiques des corrélations persistées."""
        total = (
            await self._session.execute(
                select(func.count())
                .select_from(ResourceModel)
                .where(ResourceModel.type == "correlation")
            )
        ).scalar_one()

        by_method_rows = (
            await self._session.execute(
                select(CorrelationModel.method, func.count()).group_by(CorrelationModel.method)
            )
        ).all()

        return {
            "total_correlations": total,
            **{f"methode_{method.value}": count for method, count in by_method_rows},
        }

    @staticmethod
    def _classify_strength(abs_coefficient: float) -> CorrelationStrength:
        """Classe |coefficient| selon l'échelle Evans (1996)."""
        for threshold, strength in _STRENGTH_THRESHOLDS:
            if abs_coefficient >= threshold:
                return strength
        return CorrelationStrength.negligible

    @staticmethod
    def _format_variable(variable: str, unite: str | None) -> str:
        return f"{variable} ({unite})" if unite else variable
