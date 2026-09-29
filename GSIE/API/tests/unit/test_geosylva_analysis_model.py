"""Garde-fous structurels de la file d'analyses GeoSylva."""

from gsie_api.infrastructure.models import Base


def should_register_owned_job_table_with_idempotency_and_queue_indexes() -> None:
    table = Base.metadata.tables["gsie_rgpd_identites.geosylva_analysis_job"]

    assert {"account_id", "request_id", "request_fingerprint", "lease_expires_at"} <= set(
        table.c.keys()
    )
    assert any(
        constraint.name == "uq_geosylva_analysis_account_request"
        for constraint in table.constraints
    )
    assert {index.name for index in table.indexes} >= {
        "ix_geosylva_analysis_account_status",
        "ix_geosylva_analysis_queue",
        "ix_geosylva_analysis_expiry",
    }


def should_keep_job_payloads_separate_from_immutable_analysis_run() -> None:
    table = Base.metadata.tables["gsie_rgpd_identites.geosylva_analysis_job"]

    assert "result_payload" in table.c
    assert "analysis_run_id" in table.c
    assert table.c.analysis_run_id.foreign_keys == set()
