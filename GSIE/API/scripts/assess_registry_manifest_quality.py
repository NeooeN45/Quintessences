"""Évalue sans réseau la qualité démontrable du manifeste Registry.

Le script ne persiste rien et ne promeut aucun dataset. Il expose précisément
les dimensions encore non mesurées avant la qualification scientifique.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from gsie_api.data.quality import QualityObservation, assess_quality
from gsie_api.infrastructure.models.enums import QualityDimension

REQUIRED_FIELDS = {
    "slug",
    "title",
    "description",
    "source_registry_id",
    "version",
    "primary_domain",
    "purpose",
    "status",
    "operation",
    "distribution",
}
REQUIRED_DISTRIBUTION_FIELDS = {"access_method", "access_url", "licence", "format"}


def evaluate_entry(entry: dict[str, object]) -> dict[str, object]:
    """Mesure uniquement complétude et cohérence déclarative du manifeste."""

    distribution = entry.get("distribution")
    distribution_fields = set(distribution) if isinstance(distribution, dict) else set()
    present = len(REQUIRED_FIELDS.intersection(entry)) + len(
        REQUIRED_DISTRIBUTION_FIELDS.intersection(distribution_fields)
    )
    expected = len(REQUIRED_FIELDS) + len(REQUIRED_DISTRIBUTION_FIELDS)
    completeness = present / expected
    logical = float(
        entry.get("operation") == "metadata_only"
        and entry.get("status") == "discovered"
        and completeness == 1.0
    )
    slug = str(entry.get("slug", "inconnu"))
    report = assess_quality(
        target_id=uuid5(NAMESPACE_URL, f"gsie:dataset-version:{slug}:{entry.get('version')}"),
        run_id=uuid5(NAMESPACE_URL, f"gsie:quality:registry-quality-1:{slug}"),
        observations=[
            QualityObservation(QualityDimension.completeness, completeness),
            QualityObservation(QualityDimension.logical_consistency, logical),
        ],
    )
    return {
        "slug": slug,
        "policy_version": report.policy_version,
        "complete": report.complete,
        "overall_score": report.overall_score,
        "measured": {item.dimension.value: item.score for item in report.observations},
        "missing_dimensions": [item.value for item in report.missing_dimensions],
        "promotion_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    reports = [evaluate_entry(entry) for entry in payload["entries"]]
    print(json.dumps({"reports": reports}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
