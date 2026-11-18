"""Projection scientifique publique d'une analyse GSIE.

La projection ne synthétise aucun fait nouveau. Elle réorganise seulement les
objets déjà validés et bloque les sorties d'un moteur non qualifié pour Gold.
"""

# Les annotations sont aussi utilisées par Pydantic dans les objets retournés.
# ruff: noqa: TC001, TC003

from __future__ import annotations

from datetime import datetime
from typing import Any

from gsie_api.engines.diagnostic.engine import DiagnosticEngine
from gsie_api.engines.orchestration.preparation import RapportPreparation
from gsie_api.engines.orchestration.schemas import AnalyseComplete
from gsie_api.engines.orchestration.service import OrchestrationEngine
from gsie_api.engines.reasoning.engine import ReasoningEngine
from gsie_api.engines.recommendation.engine import RecommendationEngine
from gsie_api.engines.validation.engine import ValidationEngine
from gsie_api.geosylva.schemas import EngineExecution, ScientificAnalysisResult

RECOMMENDATION_PUBLICATION_READY = False
RECOMMENDATION_WARNING = (
    "Les recommandations du moteur v1 ne sont pas publiées : son mapping déclaratif "
    "n'est pas encore relié aux règles Gold qualifiées du Knowledge Engine."
)


def _sources(analyse: AnalyseComplete) -> list[dict[str, Any]]:
    uniques: dict[str, dict[str, Any]] = {}
    for conclusion in analyse.inference.conclusions:
        for source in conclusion.sources_utilisees:
            payload = source.model_dump(mode="json")
            key = "|".join(
                str(payload.get(field, ""))
                for field in ("type_source", "auteur", "reference", "version_source")
            )
            uniques[key] = payload
    return [uniques[key] for key in sorted(uniques)]


def _observations(rapport: RapportPreparation) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    contexte = rapport.contexte_snapshot
    for name in ("geographie", "climat", "pedologie", "botanique", "peuplement"):
        block = getattr(contexte, name)
        if block is not None:
            result.append({"domain": name, **block.model_dump(mode="json")})
    result.extend(
        {"domain": "correlation", **block.model_dump(mode="json")}
        for block in contexte.correlations
    )
    return result


def _calculations(analyse: AnalyseComplete) -> list[dict[str, Any]]:
    calculations: list[dict[str, Any]] = []
    for conclusion in analyse.inference.conclusions:
        for step in conclusion.chaine_inference:
            calculations.append(
                {
                    "conclusion_id": str(conclusion.conclusion_id),
                    **step.model_dump(mode="json"),
                }
            )
    return calculations


def build_scientific_result(
    analyse: AnalyseComplete,
    rapport: RapportPreparation,
    *,
    requested_capabilities: list[str],
    started_at: datetime,
    completed_at: datetime,
    trace_id: str,
) -> ScientificAnalysisResult:
    """Construit une vue déterministe et cite directement chaque conclusion."""

    warnings: list[str] = []
    unavailable: list[str] = []
    recommendations: list[dict[str, Any]] = []
    if "recommendation" in requested_capabilities and not RECOMMENDATION_PUBLICATION_READY:
        warnings.append(RECOMMENDATION_WARNING)
        unavailable.append("recommendation")

    core = {"reasoning", "diagnostic", "recommendation", "validation"}
    for capability in sorted(set(requested_capabilities) - core):
        unavailable.append(capability)
        warnings.append(
            f"La capacité {capability} n'est pas encore branchée au snapshot stationnel V1."
        )

    present = [item["domain"] for item in _observations(rapport)]
    conclusions = [item.model_dump(mode="json") for item in analyse.inference.conclusions]
    contradictions = [item.model_dump(mode="json") for item in analyse.inference.contradictions] + [
        item.model_dump(mode="json") for item in analyse.diagnostic.contradictions
    ]
    uncertainties = list(analyse.diagnostic.incertitudes)
    if analyse.inference.resultat_partiel:
        uncertainties.append(
            "Le raisonnement a atteint sa profondeur maximale ; des règles restent non appliquées."
        )

    engines = [
        EngineExecution(engine="reasoning", version=ReasoningEngine.version(), status="completed"),
        EngineExecution(
            engine="diagnostic", version=DiagnosticEngine.version(), status="completed"
        ),
        EngineExecution(
            engine="recommendation",
            version=RecommendationEngine.version(),
            status="unavailable",
            warning=RECOMMENDATION_WARNING,
        ),
        EngineExecution(
            engine="validation", version=ValidationEngine.version(), status="completed"
        ),
        EngineExecution(
            engine="orchestration", version=OrchestrationEngine.version(), status="completed"
        ),
    ]
    duration_ms = max(int((completed_at - started_at).total_seconds() * 1000), 0)
    return ScientificAnalysisResult(
        analysis_id=analyse.analyse_id,
        request_id=analyse.requete_origine,
        station_id=rapport.station_id,
        summary=(
            f"{len(conclusions)} conclusion(s), {len(contradictions)} contradiction(s), "
            f"validation {analyse.validation.statut.value}."
        ),
        observations=_observations(rapport),
        calculations=_calculations(analyse),
        conclusions=conclusions,
        recommendations=recommendations,
        uncertainties=uncertainties,
        contradictions=contradictions,
        data_coverage={
            "present_domains": sorted(set(present)),
            "missing_domains": sorted(
                {"geographie", "climat", "pedologie", "botanique", "peuplement"} - set(present)
            ),
            "context_fingerprint": rapport.contexte_fingerprint,
        },
        sources=_sources(analyse),
        data_versions={
            "rules": rapport.regles_versions,
            "rule_fingerprints": rapport.regles_fingerprint,
            "global_state_fingerprint": rapport.etat_global_fingerprint,
            "field_intake_id": str(rapport.etat_global_field_intake),
        },
        engines=engines,
        unavailable_engines=sorted(set(unavailable)),
        warnings=warnings,
        duration_ms=duration_ms,
        trace_id=trace_id,
        completed_at=completed_at,
    )


__all__ = [
    "RECOMMENDATION_PUBLICATION_READY",
    "RECOMMENDATION_WARNING",
    "build_scientific_result",
]
