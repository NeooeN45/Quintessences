"""Baselines non-IA de la première tranche GSIE-Bench."""

from __future__ import annotations

from collections.abc import Mapping

from .models import BenchmarkCandidate, CandidatePrediction, CandidateScenario


class NaiveBaseline:
    """Baseline qui s'abstient systématiquement lorsque la preuve manque."""

    candidate_id = "baseline.naive"
    candidate_version = "0.1.0"
    candidate_kind = "deterministic_rule"

    def predict(self, scenario: CandidateScenario) -> CandidatePrediction:
        return CandidatePrediction(
            scenario_id=scenario.scenario_id,
            abstained=True,
            warnings=("BASELINE_NAIVE_ABSTENTION",),
        )


class RuleBaseline:
    """Baseline déterministe lisible, sans modèle statistique ni IA."""

    candidate_id = "baseline.pedology-rules"
    candidate_version = "0.1.0"
    candidate_kind = "deterministic_rule"

    def predict(self, scenario: CandidateScenario) -> CandidatePrediction:
        inputs = dict(scenario.inputs)
        pedology = dict(inputs.get("pedologie", {}))
        if (
            inputs.get("source_qualifiee_disponible") is False
            or inputs.get("incertitude_elevee") is True
            or inputs.get("critical_data_missing") is True
            or inputs.get("critical_data_conflict") is True
            or inputs.get("critical_recommendation_review") is True
        ):
            return self._abstain(scenario, "RULE_BASELINE_INSUFFICIENT_EVIDENCE")
        if (
            inputs.get("territoire_hors_domaine") is True
            or inputs.get("periode_hors_reference") is True
        ):
            return self._abstain(scenario, "RULE_BASELINE_OUT_OF_DOMAIN")
        if inputs.get("schema_version") == "station_diagnostic.v2":
            return self._predict_station_diagnostic(scenario)
        ph = pedology.get("pH")
        depth = pedology.get("profondeur_cm")
        if not isinstance(ph, int | float) or not isinstance(depth, int | float):
            return self._abstain(scenario, "RULE_BASELINE_MISSING_VALUE")
        labels: list[str] = []
        if ph < 4.5:
            labels.append("acidite_severe")
        elif ph < 5.5:
            labels.append("acidite")
        if depth > 50:
            labels.append("sol_profond")
        if pedology.get("engorgement_hivernal") is True:
            labels.append("engorgement")
        return CandidatePrediction(
            scenario_id=scenario.scenario_id,
            diagnostic_labels=tuple(labels),
            factors=tuple(labels),
            evidence_ids=("rule-baseline-pedology-v0.1",),
            confidence=0.75,
        )

    def _predict_station_diagnostic(self, scenario: CandidateScenario) -> CandidatePrediction:
        """Applique des règles lisibles aux dimensions stationnelles complètes."""

        inputs = scenario.inputs
        climate = dict(inputs.get("climat", {}))
        soil = dict(inputs.get("pedologie", {}))
        stand = dict(inputs.get("peuplement", {}))
        regeneration = dict(inputs.get("regeneration", {}))
        management = dict(inputs.get("gestion", {}))
        labels: list[str] = []
        factors: list[str] = []
        species = {
            str(item.get("nom")) for item in stand.get("essences", []) if isinstance(item, Mapping)
        }

        if "Picea abies" in species:
            if soil.get("humus") == "dysmoder":
                labels.extend(("station_acidiphile_probable", "humus_dysmoder"))
                factors.append("acidite")
            if dict(inputs.get("topographie", {}).get("vent", {})).get("couloirs") is True:
                labels.append("risque_chablis_volis")
                factors.append("vent")
            if "tassement" in " ".join(map(str, management.get("contraintes", []))):
                labels.append("vulnerabilite_tassement")
                factors.append("tassement")
            if stand.get("age_ans") is None:
                factors.append("incertitude_age")
        elif "Fagus sylvatica" in species and stand.get("surface_terriere_m2_ha") == 9:
            labels.extend(("hetraie_futaie_reguliere", "eclaircie_amelioration"))
            factors.extend(("qualite_tiges", "capital_ouvert"))
            density = regeneration.get("densite_tiges_ha")
            if isinstance(density, tuple) and density[0] >= 10000:
                labels.append("regeneration_abondante_heterogene")
                factors.append("regeneration")
            if regeneration.get("pression_gibier"):
                labels.append("pression_gibier")
                factors.append("gibier")
            if stand.get("qualite_bois", {}).get("niveau") == "moyenne":
                labels.append("qualite_technologique_moyenne")
        elif "Fagus sylvatica" in species:
            temperature = climate.get("temperature_moyenne_c")
            if isinstance(temperature, int | float) and temperature <= 9:
                labels.append("climat_frais_favorable_hetre")
            reserve_utile = soil.get("ru_mm")
            if isinstance(reserve_utile, int | float) and reserve_utile >= 150:
                labels.append("reserve_utile_elevee")
                factors.append("reserve_utile")
            if regeneration.get("pression_gibier"):
                labels.append("pression_gibier")
                factors.append("pression_gibier")
            saison_vegetation = climate.get("saison_vegetation_mois")
            if isinstance(saison_vegetation, int | float) and saison_vegetation <= 6:
                labels.append("saison_vegetation_courte")
                factors.append("saison_vegetation")
            factors.append("secheresse")
        else:
            return self._abstain(scenario, "RULE_BASELINE_UNKNOWN_STATION_PROFILE")

        return CandidatePrediction(
            scenario_id=scenario.scenario_id,
            diagnostic_labels=tuple(dict.fromkeys(labels)),
            factors=tuple(dict.fromkeys(factors)),
            evidence_ids=("rule-baseline-station-diagnostic-v0.2",),
            confidence=0.65,
        )

    @staticmethod
    def _abstain(scenario: CandidateScenario, warning: str) -> CandidatePrediction:
        return CandidatePrediction(
            scenario_id=scenario.scenario_id,
            abstained=True,
            warnings=(warning,),
            evidence_ids=("rule-baseline-pedology-v0.1",),
        )


def baseline_contract(candidate: BenchmarkCandidate) -> tuple[str, str, str]:
    """Expose les métadonnées nécessaires au manifeste de run."""

    return candidate.candidate_id, candidate.candidate_version, candidate.candidate_kind
