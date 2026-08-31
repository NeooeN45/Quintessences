"""Valide un paquet ``forge_analysis_bundle.v1`` avant son ingestion GSIE.

Le script est un gate local/CI : il ne contacte aucun fournisseur et n'écrit
pas dans la base. Il vérifie que Forge et GSIE calculent la même empreinte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Fichier JSON Forge à valider")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        bundle = load_analysis_bundle(args.bundle)
    except AnalysisBundleContractError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(
        json.dumps(
            {
                "valid": True,
                "schema_version": bundle.schema_version,
                "bundle_id": str(bundle.bundle_id),
                "station_id": str(bundle.station_id),
                "profile_id": bundle.profile_id,
                "source_count": len(bundle.sources),
                "parameter_count": len(bundle.parameters),
                "derived_feature_count": len(bundle.derived_features),
                "fingerprint": bundle.fingerprint(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from gsie_api.data.analysis_bundle import AnalysisBundleContractError, load_analysis_bundle

    raise SystemExit(main())
