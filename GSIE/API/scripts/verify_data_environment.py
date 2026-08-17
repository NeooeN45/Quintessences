#!/usr/bin/env python3
"""Vérifie le cloisonnement déclaratif d'un environnement GSIE.

Le contrôle est volontairement sans réseau et sans écriture : il vérifie les
identifiants de rôle, namespace, base PostgreSQL, bucket objet et projet
Compose avant tout démarrage ou test.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gsie_api.core.data_environment import validate_data_environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--database-role", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--object-bucket", required=True)
    parser.add_argument("--compose-project", required=True)
    args = parser.parse_args()
    errors = validate_data_environment(
        environment=args.environment,
        database_role=args.database_role,
        namespace=args.namespace,
        database_url=args.database_url,
        object_bucket=args.object_bucket,
        compose_project=args.compose_project,
    )
    if errors:
        print("ISOLATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    print("ISOLATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
