"""Importe un bundle Forge validé dans GSIE TEST, en quarantaine."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

from gsie_api.core.config import get_settings
from gsie_api.data.analysis_bundle import load_analysis_bundle
from gsie_api.data.analysis_bundle_import import ForgeAnalysisBundleImporter
from gsie_api.infrastructure.database import async_session_factory


async def _import(path: Path, *, submitted_by: UUID, operator_role: str, trace_id: str) -> None:
    settings = get_settings()
    bundle = load_analysis_bundle(path)
    async with async_session_factory() as session, session.begin():
        result = await ForgeAnalysisBundleImporter(
            session,
            database_role=settings.database_role,
            allowed_profiles=settings.forge_analysis_bundle_allowed_profiles,
        ).import_bundle(
            bundle,
            submitted_by=submitted_by,
            authorized_roles={operator_role},
            application_version="gsie-cli",
            trace_id=trace_id,
        )
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Bundle JSON produit par Forge")
    parser.add_argument("--submitted-by", required=True, type=UUID, help="UUID de l'opérateur")
    parser.add_argument(
        "--operator-role",
        required=True,
        choices=("writer", "admin"),
        help="Rôle d'autorisation de l'opérateur",
    )
    parser.add_argument("--trace-id", default="", help="Identifiant de traçabilité")
    args = parser.parse_args()
    asyncio.run(
        _import(
            args.bundle,
            submitted_by=args.submitted_by,
            operator_role=args.operator_role,
            trace_id=args.trace_id,
        )
    )


if __name__ == "__main__":
    main()
