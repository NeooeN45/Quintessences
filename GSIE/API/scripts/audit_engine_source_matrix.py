"""Audit CI sans réseau des dépendances des 14 moteurs GSIE."""

from __future__ import annotations

import json
import sys

from gsie_api.governance.engine_source_matrix import audit_engine_source_matrix


def main() -> int:
    """Affiche la matrice moteur -> source et bloque les incohérences."""

    audit = audit_engine_source_matrix()
    payload = {
        "valid": audit.valid,
        "engine_count": len(audit.bindings),
        "counts": audit.counts,
        "errors": list(audit.errors),
        "bindings": [
            {
                "engine_id": item.engine_id,
                "mode": item.mode.value,
                "source_ids": list(item.source_ids),
                "purpose": item.purpose,
                "candidate_sources": list(item.candidate_sources),
                "pending_source_ids": list(item.pending_source_ids),
            }
            for item in audit.bindings
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if audit.valid else 2


if __name__ == "__main__":
    sys.exit(main())
