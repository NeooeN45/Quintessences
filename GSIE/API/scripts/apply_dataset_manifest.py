#!/usr/bin/env python3
"""Prévisualise ou applique le manifeste Data Registry dans PostgreSQL.

Par défaut, le script reste en ``dry-run``. L'option ``--apply`` est la seule
qui autorise l'écriture. Aucun téléchargement n'est réalisé par ce script :
les contrôles de santé et les actifs doivent être fournis explicitement dans
des JSON produits par un adapter ou un job déjà contrôlé.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, cast

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gsie_api.data.manifest_application import (  # noqa: E402
    ManifestApplicationError,
    ManifestAssetInput,
    ManifestHealthSnapshot,
    ManifestRegistryService,
)
from gsie_api.infrastructure.database import async_session_factory  # noqa: E402
from gsie_api.ingestion.manifest import load_manifest  # noqa: E402


def _load_mapping(path: Path, model: type[Any]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Impossible de lire {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalide dans {path} à la ligne {exc.lineno}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} doit contenir un objet clé → snapshot")
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError(f"{path} contient une entrée non conforme pour {key!r}")
        result[key] = model.model_validate(value)
    return result


async def _run(
    manifest_path: Path,
    *,
    apply: bool,
    health_path: Path | None,
    assets_path: Path | None,
) -> dict[str, object]:
    manifest = load_manifest(manifest_path)
    health_reports = (
        _load_mapping(health_path, ManifestHealthSnapshot) if health_path is not None else {}
    )
    assets = _load_mapping(assets_path, ManifestAssetInput) if assets_path is not None else {}
    async with async_session_factory() as session:
        service = ManifestRegistryService(session)
        if apply:
            async with session.begin():
                report = await service.apply(
                    manifest,
                    dry_run=False,
                    health_reports=health_reports,
                    assets=assets,
                )
        else:
            report = await service.apply(
                manifest,
                dry_run=True,
                health_reports=health_reports,
                assets=assets,
            )
    return report.as_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="chemin du manifeste JSON")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="écrire dans PostgreSQL (sans cette option, aucun octet n'est modifié)",
    )
    parser.add_argument(
        "--health-json",
        type=Path,
        help="objet JSON slug/source_registry_id → snapshot DatasetHealth",
    )
    parser.add_argument(
        "--assets-json",
        type=Path,
        help="objet JSON slug/source_registry_id → actif déjà archivé",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        report = asyncio.run(
            _run(
                args.manifest,
                apply=args.apply,
                health_path=args.health_json,
                assets_path=args.assets_json,
            )
        )
    except (ManifestApplicationError, ValueError) as exc:
        print(f"MANIFESTE NON APPLIQUÉ : {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - garde opérateur DB
        print(f"ÉCHEC TECHNIQUE : {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        mode = "APPLICATION" if args.apply else "DRY-RUN"
        print(
            f"{mode} manifeste v{report['manifest_version']} — "
            f"{report['entries']} entrée(s), "
            f"{report['created_resources']} ressource(s) à créer/créée(s), "
            f"{report['updated_resources']} mise(s) à jour"
        )
        for item in cast(list[dict[str, object]], report["items"]):
            print(f"- {item['slug']}@{item['version']} : {item['action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
