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

import math
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import numpy as np
from numpy.random import Generator
from scipy import stats as scipy_stats
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.engines.correlation.schemas import (
    CorrelationComputeRequest,
    CorrelationMatrixRequest,
    CorrelationMatrixResult,
    CorrelationResult,
    PairwiseCorrelation,
    RefutationResult,
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

    def __init__(self, session: AsyncSession, rng: Generator | None = None) -> None:
        self._session = session
        self._rng = rng or np.random.default_rng()

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

        # Une série de variance nulle (même altitude, même exposition sur tous
        # les relevés) rend un coefficient indéfini : scipy renvoie NaN. Le
        # laisser passer journalisait une corrélation « nan » puis échouait à la
        # validation du schéma, donc en 500 opaque. Une variable constante n'est
        # pas une panne, c'est une entrée dégénérée : on la nomme.
        if math.isnan(coefficient) or math.isnan(p_valeur):
            raise CorrelationEngineError(
                "Coefficient de corrélation non défini : au moins une des deux "
                "variables est constante (variance nulle) — aucune relation ne "
                "peut être établie sur une série sans variation"
            )

        if p_valeur >= request.seuil_significativite:
            type_relation = TypeRelation.non_significative
        else:
            type_relation = TypeRelation.positive if coefficient > 0 else TypeRelation.negative

        strength = self._classify_strength(abs(coefficient))
        confidence = max(0.0, min(1.0, 1.0 - p_valeur))
        n_observations = len(request.variable_a.valeurs)
        now = datetime.now(UTC)
        correlation_id = uuid4()

        refutation = None
        if request.avec_refutation:
            refutation = self._refute(
                method_func,
                request.variable_a.valeurs,
                request.variable_b.valeurs,
                coefficient,
                request.n_permutations,
                request.seuil_significativite,
            )

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
            "refutation": refutation.model_dump(mode="json") if refutation else None,
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
            refutation=refutation,
        )

    async def compute_matrix(self, request: CorrelationMatrixRequest) -> CorrelationMatrixResult:
        """Calcule une matrice de corrélations pairwise N×N.

        Pour Pearson : utilise numpy.corrcoef (vectorisé BLAS) pour la
        matrice de coefficients, puis scipy.stats.t.sf pour les p-valeurs
        (formule t = r*sqrt((n-2)/(1-r²)), vectorisée). Gain : 326x à
        1521x vs scipy pairwise (benchmark BENCHMARK_CORRELATION_ENGINE).

        Pour Spearman/Kendall : scipy pairwise (plus lent mais nécessaire
        — pas d'équivalent numpy vectorisé direct).

        Ne persiste PAS les corrélations individuelles (une matrice 120
        variables = 7140 paires — la persistance massive sera ajoutée
        avec le graphe v7). Seules les paires significatives sont
        retournées dans la réponse.

        Raises:
            CorrelationEngineError: si la méthode n'est pas supportée ou
                si une variable est constante (variance nulle).
        """
        if request.methode not in _METHOD_FUNCS:
            raise CorrelationEngineError(
                f"Méthode {request.methode.value} non calculable par ce moteur "
                f"— méthodes supportées : {[m.value for m in _METHOD_FUNCS]}"
            )

        n_vars = len(request.variables)
        n_obs = len(request.variables[0].valeurs)
        labels = [self._format_variable(var.variable, var.unite) for var in request.variables]

        # Construction de la matrice de données (n_vars × n_obs)
        data = np.array([var.valeurs for var in request.variables], dtype=float)

        # Vérification variance nulle
        stds = np.std(data, axis=1)
        constant_vars = [labels[i] for i in range(n_vars) if stds[i] == 0]
        if constant_vars:
            raise CorrelationEngineError(
                f"Variable(s) constante(s) (variance nulle) : {constant_vars} — "
                f"aucune corrélation ne peut être établie sur une série sans variation"
            )

        # Calcul de la matrice de corrélation
        if request.methode == CorrelationMethod.pearson:
            corr_matrix, pval_matrix = self._pearson_matrix_vectorized(data, n_obs)
        else:
            corr_matrix, pval_matrix = self._pairwise_matrix_scipy(
                data, request.methode, n_vars, n_obs
            )

        # Construction de la matrice de sortie (diagonale = None)
        matrix_out: list[list[float | None]] = []
        for i in range(n_vars):
            row: list[float | None] = []
            for j in range(n_vars):
                if i == j:
                    row.append(None)
                else:
                    row.append(round(float(corr_matrix[i, j]), 6))
            matrix_out.append(row)

        # Extraction des paires significatives
        seuil_force_value = self._strength_threshold_value(request.seuil_force)
        significant_pairs: list[PairwiseCorrelation] = []
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                coeff = float(corr_matrix[i, j])
                p_val = float(pval_matrix[i, j])
                if math.isnan(coeff) or math.isnan(p_val):
                    continue
                abs_coeff = abs(coeff)
                if abs_coeff < seuil_force_value:
                    continue
                if p_val >= request.seuil_significativite:
                    continue
                strength = self._classify_strength(abs_coeff)
                type_rel = TypeRelation.positive if coeff > 0 else TypeRelation.negative
                significant_pairs.append(
                    PairwiseCorrelation(
                        variable_a=labels[i],
                        variable_b=labels[j],
                        coefficient=round(coeff, 6),
                        p_valeur=round(p_val, 6),
                        type_relation=type_rel,
                        strength=strength,
                        n_observations=n_obs,
                    )
                )

        # Tri par |coefficient| décroissant
        significant_pairs.sort(key=lambda p: abs(p.coefficient), reverse=True)

        n_pairs_total = n_vars * (n_vars - 1) // 2

        logger.info(
            "correlation_matrix_computed",
            requete_id=str(request.requete_id),
            methode=request.methode.value,
            n_variables=n_vars,
            n_observations=n_obs,
            n_paires_total=n_pairs_total,
            n_paires_significatives=len(significant_pairs),
        )

        return CorrelationMatrixResult(
            requete_origine=request.requete_id,
            methode=request.methode,
            n_variables=n_vars,
            n_observations=n_obs,
            n_paires_total=n_pairs_total,
            n_paires_significatives=len(significant_pairs),
            matrice=matrix_out,
            variables=labels,
            paires_significatives=significant_pairs,
            domaine_validite=request.domaine_validite,
            source=request.source,
            evidence_level=request.evidence_level,
        )

    @staticmethod
    def _pearson_matrix_vectorized(data: np.ndarray, n_obs: int) -> tuple[np.ndarray, np.ndarray]:
        """Calcule la matrice Pearson + p-valeurs vectorisées.

        Utilise numpy.corrcoef (BLAS) pour les coefficients, puis
        scipy.stats.t.sf pour les p-valeurs (formule t-distribution).
        """
        corr_matrix = np.corrcoef(data)
        # p-valeur : p = 2 * t.sf(|t|, df=n-2) où t = r * sqrt((n-2)/(1-r²))
        df = n_obs - 2
        # Éviter division par zéro pour r = ±1
        r_squared = corr_matrix**2
        r_squared = np.clip(r_squared, 0.0, 0.999999)
        t_stat = corr_matrix * np.sqrt(df / (1.0 - r_squared))
        pval_matrix = 2.0 * scipy_stats.t.sf(np.abs(t_stat), df)
        return corr_matrix, pval_matrix

    @staticmethod
    def _pairwise_matrix_scipy(
        data: np.ndarray,
        methode: CorrelationMethod,
        n_vars: int,
        n_obs: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Calcule la matrice Spearman/Kendall via scipy pairwise.

        Fallback pour méthodes de rang — pas d'équivalent numpy vectorisé.
        """
        method_func = _METHOD_FUNCS[methode]
        corr_matrix = np.full((n_vars, n_vars), np.nan)
        pval_matrix = np.full((n_vars, n_vars), np.nan)
        for i in range(n_vars):
            corr_matrix[i, i] = 1.0
            pval_matrix[i, i] = 0.0
            for j in range(i + 1, n_vars):
                result = method_func(data[i], data[j])
                coeff = float(result.statistic)
                p_val = float(result.pvalue)
                corr_matrix[i, j] = coeff
                corr_matrix[j, i] = coeff
                pval_matrix[i, j] = p_val
                pval_matrix[j, i] = p_val
        return corr_matrix, pval_matrix

    @staticmethod
    def _strength_threshold_value(strength: CorrelationStrength) -> float:
        """Retourne la valeur |r| minimale pour une force donnée."""
        for threshold, s in _STRENGTH_THRESHOLDS:
            if s == strength:
                return threshold
        return 0.0

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

    def _refute(
        self,
        method_func: Any,
        valeurs_a: list[float],
        valeurs_b: list[float],
        coefficient_observe: float,
        n_permutations: int,
        seuil_significativite: float,
    ) -> RefutationResult:
        """Test de réfutation par permutation — RFC-0015 §3.5, étape 6.

        Mélange `valeurs_b` `n_permutations` fois (brise tout lien réel
        tout en conservant chaque distribution marginale), recalcule le
        coefficient à chaque tirage, et compare le coefficient observé à
        cette distribution « placebo ». Aucune dépendance externe (DoWhy
        non installé — voir RFC-0015 §3.5, candidat à benchmarker avant
        adoption formelle) : implémentation directe du même principe
        statistique (permutation/placebo test).
        """
        array_b = np.array(valeurs_b, dtype=float)
        coefficients_placebo = np.empty(n_permutations)
        for i in range(n_permutations):
            permuted = self._rng.permutation(array_b)
            coefficients_placebo[i] = float(method_func(valeurs_a, permuted).statistic)

        n_extreme = int(np.sum(np.abs(coefficients_placebo) >= abs(coefficient_observe)))
        p_valeur_permutation = (n_extreme + 1) / (n_permutations + 1)  # correction +1 standard
        robuste = p_valeur_permutation < seuil_significativite

        interpretation = (
            "association observée, robuste au test de permutation"
            if robuste
            else "association observée, non robuste au test de permutation"
        )

        return RefutationResult(
            n_permutations=n_permutations,
            p_valeur_permutation=p_valeur_permutation,
            robuste=robuste,
            interpretation=interpretation,
        )

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
