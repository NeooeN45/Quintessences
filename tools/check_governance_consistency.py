#!/usr/bin/env python3
"""Garde-fou de gouvernance GSIE — vérifie que le dépôt ne se contredit pas lui-même.

Trois règles, dérivées directement de CLAUDE.md et de la Constitution GSIE :

1. Intégrité des références : toute mention d'un RFC-XXXX / DEC-XXXXXX / ADR-XXX
   dans un document de gouvernance doit pointer vers un fichier qui existe,
   OU être définie en interne (section « ## N. ADR-XXXX » dans un document
   comme TECHNOLOGY_STACK.md), OU être explicitement documentée comme
   remplacée/supersédée. (« Aucune décision perdue », traçabilité CON-005.)

2. Décision → Implémentation : si une DEC-XXXXXX ou une RFC-XXXX n'a pas
   encore un statut adopté (Validé/Adopté/Verrouillé), aucun fichier
   d'implémentation (migrations Alembic, modèles infra) ne doit s'y référer
   comme base déjà actée (CON-003 : « la connaissance avant le code » ;
   hiérarchie Décision avant Implémentation).

3. Valeurs non sourcées (ADR-007) : dans les moteurs de raisonnement
   (`engines/*/engine.py`), toute constante module-level contenant un
   littéral décimal (seuil, coefficient) doit avoir une citation détectable
   (« Nom (Année) », « Nom et al. (Année) », ou référence RFC-/ADR-/DEC-/
   CON-) dans les 5 lignes qui la précèdent. Détection best-effort — ne
   prouve pas l'absence de donnée inventée, attrape les cas évidents.

Usage : python tools/check_governance_consistency.py
Code de sortie : 0 si rien à signaler, 1 si au moins une violation trouvée.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

ADOPTED_STATUSES = {
    "validé", "valide", "validated", "adopté", "adopte", "adopted",
    "accepté", "accepte", "accepted", "locked", "verrouillé", "verrouille",
}

ID_PATTERN = re.compile(r"\b(RFC-\d{4}|DEC-\d{6}|ADR-\d{3,4})\b")
STATUS_PATTERN = re.compile(
    r"\*\*Statut\*\*\s*\|\s*([^\|\n]+)|Statut\s*:\s*([^\n]+)", re.IGNORECASE
)
# Définition interne (section « ## N. ADR-0001 — ... » ou ligne « **ID** | ADR-0001 »)
# — un ADR peut être documenté comme sous-section d'un autre fichier (ex.
# TECHNOLOGY_STACK.md) plutôt que comme fichier séparé.
INLINE_DEF_PATTERN = re.compile(
    r"(?:^#{1,6}[^\n]*|\*\*ID\*\*\s*\|[^\n]*)\b(RFC-\d{4}|DEC-\d{6}|ADR-\d{3,4})\b",
    re.MULTILINE,
)
# Un identifiant mentionné à proximité de « remplacé(s) par »/« supersédé(s) par »
# est considéré comme tracé (traçabilité satisfaite), même sans fichier séparé —
# c'est le cas des ADR-0008..0013 jamais rédigés, retirés avant adoption.
SUPERSEDE_PATTERN = re.compile(r"remplac\w*|superséd\w*|supersed\w*", re.IGNORECASE)

GOVERNANCE_DIRS = ["02_RFC", "03_DECISIONS", "GSIE/ARCHITECTURE"]
IMPLEMENTATION_GLOBS = [
    "GSIE/API/alembic/versions/*.py",
    "GSIE/API/src/gsie_api/infrastructure/models/*.py",
    "GSIE/API/src/gsie_api/infrastructure/models.py",
    "GSIE/API/src/gsie_api/infrastructure/knowledge_models.py",
]

# Règle 3 (ADR-007) — moteurs de raisonnement à auditer pour valeurs non sourcées
REASONING_ENGINE_GLOBS = ["GSIE/API/src/gsie_api/engines/*/engine.py"]
# Citation détectable : « Nom (Année) », « Nom et al. (Année) », ou référence
# de gouvernance (RFC-/ADR-/DEC-/CON-).
CITATION_PATTERN = re.compile(
    r"[A-Z][a-zA-Z\-]+(?:\s+et al\.?)?\s*\(\d{4}\)|\b(?:RFC-\d{4}|DEC-\d{6}|ADR-\d{3,4}|CON-\d{3})\b"
)
FLOAT_LITERAL_PATTERN = re.compile(r"\d+\.\d+")
CONSTANT_DEF_PATTERN = re.compile(r"^(_[A-Z][A-Z0-9_]*)\s*(?::[^=]+)?=\s*(.+)$")
_CITATION_LOOKBACK_LINES = 5


def find_doc_file(doc_id: str) -> Path | None:
    """Cherche le fichier correspondant à un identifiant RFC/DEC/ADR."""
    for base in ["02_RFC", "03_DECISIONS", "GSIE/ARCHITECTURE"]:
        for path in (ROOT / base).rglob(f"{doc_id}*.md"):
            return path
    return None


def extract_status(text: str) -> str | None:
    match = STATUS_PATTERN.search(text)
    if not match:
        return None
    raw = (match.group(1) or match.group(2) or "").strip()
    # Garde le premier mot significatif (ex. "Proposé" dans "Proposé (soumis à RFC-0011)")
    first_word = re.split(r"[\s(,]", raw)[0].strip().lower()
    return first_word


def find_superseded_ids(text: str) -> set[str]:
    """IDs mentionnés à proximité d'un « remplacé par »/« supersédé par » — tracés,
    même sans fichier séparé (ex. anciens ADR jamais rédigés, retirés avant adoption)."""
    ids: set[str] = set()
    for match in SUPERSEDE_PATTERN.finditer(text):
        window = text[max(0, match.start() - 200) : match.end() + 200]
        ids.update(ID_PATTERN.findall(window))
    return ids


def find_unsourced_numeric_constants(text: str) -> list[str]:
    """Détecte les constantes module-level à littéral décimal sans citation proche.

    Best-effort (ADR-007) : repère les blocs `_NOM = ...` (éventuellement
    multi-lignes, listes/dicts inclus) contenant un nombre décimal, et
    vérifie qu'une citation (« Nom (Année) » ou référence de gouvernance)
    apparaît dans les quelques lignes qui précèdent — typiquement un
    commentaire expliquant la source du seuil/coefficient.
    """
    lines = text.split("\n")
    findings: list[str] = []
    i = 0
    while i < len(lines):
        match = CONSTANT_DEF_PATTERN.match(lines[i])
        if not match:
            i += 1
            continue
        name = match.group(1)
        block_lines = [lines[i]]
        depth = sum(lines[i].count(c) for c in "([{") - sum(lines[i].count(c) for c in ")]}")
        j = i
        while depth > 0 and j + 1 < len(lines):
            j += 1
            block_lines.append(lines[j])
            depth += sum(lines[j].count(c) for c in "([{") - sum(lines[j].count(c) for c in ")]}")
        block_text = "\n".join(block_lines)
        if "SourceReference(" in block_text:
            # Une SourceReference EST la citation structurée (auteur,
            # date_publication, reference en kwargs) — pas de prose
            # "Nom (Année)" à chercher, la structure elle-même en tient lieu.
            i = j + 1
            continue
        if FLOAT_LITERAL_PATTERN.search(block_text):
            context_start = max(0, i - _CITATION_LOOKBACK_LINES)
            context = "\n".join(lines[context_start:i])
            if not CITATION_PATTERN.search(context) and not CITATION_PATTERN.search(block_text):
                findings.append(name)
        i = j + 1
    return findings


def main() -> int:
    violations: list[str] = []

    all_doc_files: list[Path] = []
    for d in GOVERNANCE_DIRS:
        all_doc_files.extend((ROOT / d).rglob("*.md"))

    # --- Passe préalable : identifiants « connus » (fichier, définition
    # interne, ou explicitement documentés comme remplacés/supersédés) ---
    known_ids: set[str] = set()
    doc_status: dict[str, str] = {}
    doc_texts: dict[Path, str] = {}
    for path in all_doc_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        doc_texts[path] = text
        own_ids = set(ID_PATTERN.findall(path.stem)) or set(ID_PATTERN.findall(text[:200]))
        status = extract_status(text)
        if status:
            for oid in own_ids:
                doc_status[oid] = status
        known_ids.update(own_ids)
        known_ids.update(INLINE_DEF_PATTERN.findall(text))
        known_ids.update(find_superseded_ids(text))

    # --- Règle 1 : intégrité des références ---
    for path in all_doc_files:
        text = doc_texts[path]
        own_ids = set(ID_PATTERN.findall(path.stem)) or set(ID_PATTERN.findall(text[:200]))

        for ref_id in set(ID_PATTERN.findall(text)):
            if ref_id in own_ids or ref_id in known_ids:
                continue
            if find_doc_file(ref_id) is None:
                violations.append(
                    f"[réf. cassée] {path.relative_to(ROOT)} référence {ref_id}, "
                    f"introuvable (ni fichier, ni définition interne, ni mention "
                    f"« remplacé par »)."
                )

    # --- Règle 2 : implémentation avant décision adoptée ---
    not_adopted = {
        doc_id for doc_id, status in doc_status.items() if status not in ADOPTED_STATUSES
    }

    impl_files: list[Path] = []
    for pattern in IMPLEMENTATION_GLOBS:
        impl_files.extend(ROOT.glob(pattern))

    for path in impl_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for ref_id in set(ID_PATTERN.findall(text)):
            if ref_id in not_adopted:
                violations.append(
                    f"[implémentation prématurée] {path.relative_to(ROOT)} référence "
                    f"{ref_id}, dont le statut est encore « {doc_status[ref_id]} » "
                    f"(pas Validé/Adopté) — l'implémentation ne doit pas précéder "
                    f"la décision (CON-003)."
                )

    # --- Règle 3 (ADR-007) : valeurs numériques potentiellement non sourcées ---
    reasoning_files: list[Path] = []
    for pattern in REASONING_ENGINE_GLOBS:
        reasoning_files.extend(ROOT.glob(pattern))

    for path in reasoning_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in find_unsourced_numeric_constants(text):
            violations.append(
                f"[valeur non sourcée] {path.relative_to(ROOT)} : la constante {name} "
                f"contient un littéral décimal sans citation détectée dans les "
                f"{_CITATION_LOOKBACK_LINES} lignes précédentes (ADR-007) — vérifier "
                f"qu'elle est bien sourcée."
            )

    if not violations:
        print("OK — aucune incohérence de gouvernance détectée.")
        return 0

    print(f"{len(violations)} incohérence(s) de gouvernance détectée(s) :\n")
    for v in violations:
        print(f"  - {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
