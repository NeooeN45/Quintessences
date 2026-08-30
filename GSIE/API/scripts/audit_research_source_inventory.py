"""Audit sans réseau de la réconciliation des sources de recherche D1 à D8."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_NAME_PATTERN = re.compile(r"^\| \*\*Nom officiel\*\* \| (?P<name>.*?) \|$")
_PRIORITY_PATTERN = re.compile(r"^\| \*\*Priorité GSIE\*\* \| (?P<priority>.*?) \|$")


@dataclass(frozen=True, slots=True)
class ResearchSourceRecord:
    """Source documentée mais non promue par ce simple inventaire."""

    source_file: str
    ordinal: int
    name: str
    priority: str

    @property
    def candidate_id(self) -> str:
        """Identifiant local, distinct d'un identifiant SCI-001."""

        stem = Path(self.source_file).stem
        return f"research:{stem}:{self.ordinal:03d}"


@dataclass(frozen=True, slots=True)
class ResearchSourceInventoryAudit:
    """Résultat du parsing déterministe des inventaires de recherche."""

    records: tuple[ResearchSourceRecord, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Indique qu'aucune fiche documentée n'est incomplète."""

        return not self.errors

    @property
    def unique_name_count(self) -> int:
        """Compte les noms distincts sans supprimer les occurrences."""

        return len({record.name.casefold() for record in self.records})


def audit_research_source_inventory(root: Path) -> ResearchSourceInventoryAudit:
    """Extrait les noms et priorités des documents D1 à D8.

    Le résultat reste un inventaire de candidats. Aucune ligne n'est ajoutée
    automatiquement à SCI-001, ce qui évite d'inventer une licence ou un droit
    de redistribution à partir d'une documentation de recherche.
    """

    source_dir = root / "GSIE" / "RESEARCH" / "SOURCES"
    records: list[ResearchSourceRecord] = []
    errors: list[str] = []
    for path in sorted(source_dir.glob("sources_*.md")):
        pending_name: str | None = None
        ordinal = 0
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            name_match = _NAME_PATTERN.match(line)
            if name_match:
                if pending_name is not None:
                    errors.append(f"RESEARCH_SOURCE_MISSING_PRIORITY:{path}:{line_number}")
                pending_name = " ".join(name_match.group("name").split())
                continue
            priority_match = _PRIORITY_PATTERN.match(line)
            if priority_match and pending_name is not None:
                ordinal += 1
                records.append(
                    ResearchSourceRecord(
                        source_file=path.as_posix(),
                        ordinal=ordinal,
                        name=pending_name,
                        priority=" ".join(priority_match.group("priority").split()),
                    )
                )
                pending_name = None
        if pending_name is not None:
            errors.append(f"RESEARCH_SOURCE_MISSING_PRIORITY:{path}:EOF")

    if not records:
        errors.append("RESEARCH_SOURCE_INVENTORY_EMPTY")
    return ResearchSourceInventoryAudit(tuple(records), tuple(sorted(errors)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    audit = audit_research_source_inventory(args.root.resolve())
    payload = {
        "valid": audit.valid,
        "documented_count": len(audit.records),
        "unique_name_count": audit.unique_name_count,
        "errors": list(audit.errors),
        "candidates": [
            {
                "candidate_id": record.candidate_id,
                "source_file": record.source_file,
                "name": record.name,
                "priority": record.priority,
                "status": "CANDIDATE_METADATA_ONLY",
            }
            for record in audit.records
        ],
    }
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if audit.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
