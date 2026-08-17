"""Scénarios de cohérence interne issus des fiches terrain BTS.

Ces scénarios restent en quarantaine : ils testent la capacité d'abstention
et la traçabilité d'une contradiction, sans devenir une vérité Gold.
"""

from __future__ import annotations

from typing import Any

from .catalog import REFERENCE_BTS_FICHE
from .models import ScenarioSpec


def build_dendrometry_conflict_catalog() -> tuple[ScenarioSpec, ...]:
    """Construit le scénario contradictoire Farges, versionné et non-Gold."""

    inputs: dict[str, Any] = {
        "schema_version": "station_diagnostic.v2",
        "provenance": {
            "observed": ["bts-fiche-diagnostic-stationnel-camille-2026"],
            "derived": ["field_intake_station.v0.1"],
            "missing": ["diameter_distribution", "sampling_design"],
            "review_required": ["expert_dendrometry", "rights_annotation"],
        },
        "contexte": {"site": "Les Farges", "plot_id": "WA-0001"},
        "peuplement": {
            "densite_tiges_ha": 325,
            "surface_terriere_m2_ha": 20.5,
            "diametre_moyen_cm": 53,
            "methode_diametre": "dendrometry.arithmetic_mean",
        },
        "mesures_et_calculs": {
            "methode_inventaire": "inventory.manual",
            "contradiction": "diameter_vs_basal_area_density",
        },
    }
    return (
        ScenarioSpec(
            scenario_id="quarantine.farges.dendrometry.001",
            scenario_version="0.1.0",
            suite_version="0.1.0",
            level="silver",
            visibility="quarantine",
            qualification_status="pending_expert_review",
            territory="les-farges",
            period="2026",
            variation_kind="contradictory_dendrometry",
            parent_scenario_id="gold.farges.station.001",
            inputs=inputs,
            expected_labels=(),
            required_factors=("dendrometry_consistency",),
            forbidden_recommendations=("promotion_without_review",),
            expected_behavior="abstain_or_warn",
            references=(REFERENCE_BTS_FICHE,),
            rights_status="owner_provided_internal_pending_expert_review",
        ),
    )


__all__ = ["build_dendrometry_conflict_catalog"]
