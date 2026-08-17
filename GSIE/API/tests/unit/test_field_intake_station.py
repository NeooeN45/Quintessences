"""Tests du contrat FieldIntake stationnel v0.1."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from gsie_api.data.field_intake import FieldIntakeSubmission
from gsie_api.data.field_intake_station import (
    StationCalculation,
    StationIntake,
    StationObservation,
    StationRecommendation,
    check_station_consistency,
    compute_basal_area_m2_ha,
    compute_quadratic_mean_diameter_cm,
)


def should_compute_basal_area_from_diameter_and_density() -> None:
    assert compute_basal_area_m2_ha(diameter_cm=20.0, stems_per_ha=100.0) == pytest.approx(
        3.1416,
        abs=0.0001,
    )


def should_compute_quadratic_mean_diameter_from_basal_area_and_density() -> None:
    assert compute_quadratic_mean_diameter_cm(
        basal_area_m2_ha=20.5,
        stems_per_ha=325.0,
    ) == pytest.approx(
        28.36,
        abs=0.03,
    )


def should_reject_negative_dendrometric_values() -> None:
    with pytest.raises(ValidationError):
        StationObservation(
            observation_type="stems_per_ha",
            value=-1,
            unit="stems_per_ha",
            method_id="inventory.manual",
            method_version="0.1.0",
            observed_at=datetime(2026, 8, 12, tzinfo=UTC),
        )


def should_report_dendrometric_contradiction_without_rewriting_input() -> None:
    intake = StationIntake(
        context={"territory": "Farges", "plot_id": "WA-0001"},
        observations=(
            StationObservation(
                observation_type="stems_per_ha",
                value=325,
                unit="stems_per_ha",
                method_id="inventory.manual",
                method_version="0.1.0",
                observed_at=datetime(2026, 8, 12, tzinfo=UTC),
            ),
            StationObservation(
                observation_type="basal_area_m2_ha",
                value=20.5,
                unit="m2/ha",
                method_id="basal_area.sum_tree_sections",
                method_version="0.1.0",
                observed_at=datetime(2026, 8, 12, tzinfo=UTC),
            ),
            StationObservation(
                observation_type="mean_diameter_cm",
                value=53,
                unit="cm",
                method_id="dendrometry.arithmetic_mean",
                method_version="0.1.0",
                observed_at=datetime(2026, 8, 12, tzinfo=UTC),
            ),
        ),
        calculations=(
            StationCalculation(
                calculation_type="volume_m3_ha",
                value=1255,
                unit="m3/ha",
                method_id="volume.from_stem_volume",
                method_version="0.1.0",
                derived_from=("stems_per_ha", "mean_stem_volume_m3"),
            ),
        ),
        recommendations=(
            StationRecommendation(
                recommendation_id="review.dendrometry",
                text="Revoir les conventions d'inventaire et les calculs.",
                status="pending_review",
                evidence_refs=("Farges.note.terrain",),
            ),
        ),
    )

    report = check_station_consistency(intake)

    assert report.has_error is True
    assert any(issue.code == "BASAL_AREA_DIAMETER_CONTRADICTION" for issue in report.issues)
    assert intake.observations[2].value == 53


def should_reject_unknown_observation_unit() -> None:
    with pytest.raises(ValidationError):
        StationObservation(
            observation_type="pH",
            value=4.5,
            unit="arbitrary",
            method_id="soil.ph_water",
            method_version="0.1.0",
            observed_at=datetime(2026, 8, 12, tzinfo=UTC),
        )


def should_require_provenance_for_recommendation() -> None:
    with pytest.raises(ValidationError):
        StationRecommendation(
            recommendation_id="recommendation.001",
            text="Une recommandation sans justification.",
            status="pending_review",
        )


def should_embed_station_contract_in_existing_field_intake_submission() -> None:
    station = StationIntake(
        context={"plot_id": "WA-0001"},
        observations=(
            StationObservation(
                observation_type="pH",
                value=4.5,
                unit="pH",
                method_id="soil.ph_water",
                method_version="0.1.0",
                observed_at=datetime(2026, 8, 12, tzinfo=UTC),
            ),
        ),
    )
    submission = FieldIntakeSubmission(
        application_key="geosylva",
        client_event_id="evt-001",
        kind="observation",
        observed_at=datetime(2026, 8, 12, tzinfo=UTC),
        payload={"capture_mode": "manual"},
        provenance={"device": "test"},
        station=station,
    )
    assert submission.station is station
    assert submission.station.model_dump(mode="json")["schema_version"] == "station_intake.v0.1"
