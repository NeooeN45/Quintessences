"""Importe un bundle Forge qualifié dans GSIE TEST, sans réseau fournisseur."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from gsie_api.core.config import get_settings
from gsie_api.data.gsie_test_bundle import GsiePreparationBundle, GsieTestBundleImporter
from gsie_api.infrastructure.database import async_session_factory


async def _import(path: Path) -> None:
    settings = get_settings()
    bundle = GsiePreparationBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))
    async with async_session_factory() as session, session.begin():
        await GsieTestBundleImporter(session, database_role=settings.database_role).import_bundle(
            bundle
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Bundle JSON produit par Forge")
    args = parser.parse_args()
    asyncio.run(_import(args.bundle))


if __name__ == "__main__":
    main()
