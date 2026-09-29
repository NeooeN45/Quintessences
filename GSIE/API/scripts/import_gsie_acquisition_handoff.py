#!/usr/bin/env python3
"""Vérifie, archive et applique un handoff Forge dans le Data Registry GSIE."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import cast

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gsie_api.data.acquisition_handoff import (  # noqa: E402
    AcquisitionHandoffError,
    load_acquisition_handoff,
    materialize_handoff_assets,
)
from gsie_api.data.manifest_application import ManifestRegistryService  # noqa: E402
from gsie_api.infrastructure.database import async_session_factory  # noqa: E402
from gsie_api.infrastructure.object_storage import get_object_storage  # noqa: E402


async def _run(handoff_path: Path, *, staging_root: Path, apply: bool) -> dict[str, object]:
    handoff = load_acquisition_handoff(handoff_path)
    storage = get_object_storage()
    materialized = await materialize_handoff_assets(
        handoff,
        staging_root=staging_root,
        storage=storage,
        archive=apply,
    )
    assets = {slug: item.asset for slug, item in materialized.items()}
    try:
        async with async_session_factory() as session:
            service = ManifestRegistryService(session)
            if apply:
                async with session.begin():
                    report = await service.apply(
                        handoff.manifest,
                        dry_run=False,
                        assets=assets,
                    )
            else:
                report = await service.apply(
                    handoff.manifest,
                    dry_run=True,
                    assets=assets,
                )
    except BaseException:
        if apply:
            for item in materialized.values():
                if item.created:
                    await storage.delete(item.storage_key)
        raise
    return {
        "handoff_schema_version": handoff.schema_version,
        "apply": apply,
        "assets": [
            {
                "dataset_slug": item.dataset_slug,
                "storage_uri": item.asset.storage_uri,
                "created": item.created,
            }
            for item in materialized.values()
        ],
        "registry": report.as_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path, help="handoff JSON produit par Forge")
    parser.add_argument(
        "--staging-root",
        type=Path,
        help="dossier contenant les chemins relatifs du handoff (défaut : dossier du handoff)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="archiver dans ObjectStorage et appliquer dans PostgreSQL",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    staging_root = args.staging_root or args.handoff.parent
    try:
        report = asyncio.run(
            _run(args.handoff, staging_root=staging_root, apply=args.apply)
        )
    except (AcquisitionHandoffError, ValueError) as exc:
        print(f"HANDOFF NON APPLIQUÉ : {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - garde opérateur DB/storage
        print(f"ÉCHEC TECHNIQUE : {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        mode = "APPLICATION" if args.apply else "DRY-RUN"
        registry = cast(dict[str, object], report["registry"])
        assets = cast(list[dict[str, object]], report["assets"])
        print(
            f"{mode} handoff {report['handoff_schema_version']} — "
            f"{registry['entries']} entrée(s)"
        )
        for asset in assets:
            print(f"- {asset['dataset_slug']} : {asset['storage_uri']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
