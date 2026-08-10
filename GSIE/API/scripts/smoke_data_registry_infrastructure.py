#!/usr/bin/env python3
"""Smoke déterministe PostgreSQL + MinIO de la tranche Data Registry.

Le manifeste est appliqué puis rejoué dans une base jetable. Un objet borné
est ensuite écrit, relu, vérifié par SHA-256 et supprimé dans MinIO. Le script
ne contacte aucun fournisseur et n'active aucune capacité ``FETCH``.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from sqlalchemy import text

from gsie_api.data.manifest_application import ManifestRegistryService
from gsie_api.infrastructure.database import async_session_factory, engine
from gsie_api.infrastructure.object_storage import close_object_storage, get_object_storage
from gsie_api.ingestion.manifest import load_manifest

API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = API_ROOT.parent / "DATASETS" / "REGISTRY_MANIFEST.json"


async def run(manifest_path: Path) -> dict[str, object]:
    """Exécute le smoke et retourne une preuve dépourvue de secrets."""

    manifest = load_manifest(manifest_path)
    async with async_session_factory() as session:
        async with session.begin():
            database_revision = await session.scalar(
                text("SELECT version_num FROM alembic_version")
            )
            first = await ManifestRegistryService(session).apply(manifest, dry_run=False)
        async with session.begin():
            replay = await ManifestRegistryService(session).apply(manifest, dry_run=False)

    if replay.created != 0 or replay.updated != 0:
        raise RuntimeError("le rejeu du manifeste n'est pas idempotent")

    storage = get_object_storage()
    payload = json.dumps(
        {
            "manifest_version": manifest.manifest_version,
            "entries": len(manifest.entries),
            "purpose": "ci-infrastructure-smoke",
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    checksum = hashlib.sha256(payload).hexdigest()
    key = f"ci/data-registry/{uuid.uuid4().hex}/preuve.json"
    cleanup = False
    try:
        uri = await storage.put(key, BytesIO(payload), content_type="application/json")
        metadata = await storage.head(key)
        downloaded = await storage.get(key)
        try:
            roundtrip = downloaded.read()
        finally:
            downloaded.close()
        if roundtrip != payload or hashlib.sha256(roundtrip).hexdigest() != checksum:
            raise RuntimeError("le round-trip MinIO ou son checksum est incohérent")
        content_length = metadata.get("ContentLength", metadata.get("content_length"))
        if content_length != len(payload):
            raise RuntimeError("la taille déclarée par MinIO est incohérente")
    finally:
        try:
            cleanup = await storage.delete(key)
        finally:
            await close_object_storage()
            await engine.dispose()
    if not cleanup:
        raise RuntimeError("l'objet de smoke MinIO n'a pas été supprimé")

    return {
        "schema_version": "1.0",
        "checked_at": datetime.now(UTC).isoformat(),
        "database_revision": database_revision,
        "manifest": {
            "version": manifest.manifest_version,
            "entries": len(manifest.entries),
            "first_application": first.as_dict(),
            "replay": replay.as_dict(),
        },
        "object_storage": {
            "uri_scheme": uri.split(":", maxsplit=1)[0],
            "bytes": len(payload),
            "sha256": checksum,
            "roundtrip": True,
            "cleanup": True,
        },
        "fetch_performed": False,
        "succeeded": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = asyncio.run(run(args.manifest))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
