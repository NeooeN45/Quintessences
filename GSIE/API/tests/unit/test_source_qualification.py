"""Tests des portes de qualification, sans accès réseau ni base."""

from gsie_api.governance.source_qualification import (
    QualificationTarget,
    SourceQualificationProfile,
    qualification_report,
)


def _profile(**overrides: str | bool) -> SourceQualificationProfile:
    values: dict[str, str | bool] = {
        "source_id": "source-test",
        "distribution": "https://example.org/dataset",
        "version": "2026.1",
        "format": "JSON",
        "schema": "schema.v1",
        "licence_evidence": "fiche-juridique.md",
        "access_evidence": "fiche-acces.md",
        "quality_evidence": "fiche-qualite.md",
        "provenance_policy": "manifest-sha256",
        "quota_policy": "100 req/minute",
        "operator_fetch_approval": "DEC-TEST",
        "promotion_evidence": "bench-run.json",
        "expert_review": "review.md",
        "train_eval_split": "split.v1",
    }
    values.update(overrides)
    return SourceQualificationProfile(**values)


def test_une_fiche_incomplete_reste_fermee() -> None:
    profile = SourceQualificationProfile(source_id="candidate")

    assert not profile.ready(QualificationTarget.QUERY)
    assert "licence_evidence" in profile.missing(QualificationTarget.QUERY)
    assert not profile.ready(QualificationTarget.FETCH)
    assert not profile.ready(QualificationTarget.PROMOTION)


def test_une_fiche_complete_separe_query_fetch_et_promotion() -> None:
    profile = _profile()

    assert profile.ready(QualificationTarget.QUERY)
    assert profile.ready(QualificationTarget.FETCH)
    assert profile.ready(QualificationTarget.PROMOTION)


def test_une_source_spatiale_exige_un_crs() -> None:
    profile = _profile(spatial=True)

    assert not profile.ready(QualificationTarget.QUERY)
    assert profile.missing(QualificationTarget.QUERY) == ("crs",)


def test_le_rapport_est_stable_et_json_compatible() -> None:
    report = qualification_report(_profile())

    assert report["source_id"] == "source-test"
    assert report["ready_query"] is True
    assert report["missing_promotion"] == []
