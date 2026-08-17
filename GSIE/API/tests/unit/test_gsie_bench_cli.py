"""Test du rapport JSON de la CLI GSIE-Bench."""

import json

from scripts.gsie_bench import main


def should_emit_reproducible_open_silver_json_report(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["--suite", "open-silver", "--candidate", "rules"])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "GO"
    assert report["candidate_id"] == "baseline.pedology-rules"
    assert report["manifest"]["manifest_checksum"]
    assert len(report["evaluations"]) == 3
