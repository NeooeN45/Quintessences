"""Mesure reproductible des audits de gouvernance en mémoire.

Ce banc ne mesure ni le fournisseur, ni PostgreSQL, ni Forge. Il vérifie que
les contrôles de registre restent bornés lorsque le nombre de fiches
candidates augmente. Les campagnes réseau et les charges PostGIS doivent être
exécutées dans les environnements dédiés, avec leurs propres preuves.
"""

from __future__ import annotations

import argparse
import time

from gsie_api.governance.engine_source_matrix import audit_engine_source_matrix
from gsie_api.governance.source_coverage import SOURCE_COVERAGE, audit_source_coverage
from gsie_api.governance.source_registry import SCIENTIFIC_SOURCES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1000)
    args = parser.parse_args()
    if args.iterations < 1 or args.iterations > 100_000:
        parser.error("--iterations doit être compris entre 1 et 100000")

    started = time.perf_counter()
    for _ in range(args.iterations):
        if not audit_source_coverage().valid:
            return 2
        if not audit_engine_source_matrix().valid:
            return 2
    elapsed = time.perf_counter() - started
    print(f"iterations={args.iterations}")
    print(f"sources={len(SCIENTIFIC_SOURCES)}")
    print(f"coverage_entries={len(SOURCE_COVERAGE)}")
    print(f"engine_count={len(audit_engine_source_matrix().bindings)}")
    print(f"elapsed_seconds={elapsed:.6f}")
    print(f"iterations_per_second={args.iterations / elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
