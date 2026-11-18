"""Audit CI sans réseau de la couverture des sources GSIE et Forge."""

from __future__ import annotations

import json
import sys

from gsie_api.governance.source_coverage import audit_source_coverage


def main() -> int:
    """Affiche la matrice et échoue si un branchement est incohérent."""

    audit = audit_source_coverage()
    payload = {
        "valid": audit.valid,
        "source_count": len(audit.entries),
        "counts": audit.counts,
        "errors": list(audit.errors),
        "entries": [
            {
                "source_id": item.source_id,
                "status": item.status.value,
                "integration": item.integration,
                "adapter_key": item.adapter_key,
                "canonical_surface": item.canonical_surface,
                "blocking_reason": item.blocking_reason,
            }
            for item in audit.entries
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if audit.valid else 2


if __name__ == "__main__":
    sys.exit(main())
