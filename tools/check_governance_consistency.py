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

3. Valeurs non sourcées (ADR-009) : dans les moteurs de raisonnement
   (`engines/*/engine.py`), toute constante module-level contenant un
   littéral décimal (seuil, coefficient) doit avoir une citation détectable
   (« Nom (Année) », « Nom et al. (Année) », ou référence RFC-/ADR-/DEC-/
   CON-) dans les 5 lignes qui la précèdent. Détection best-effort — ne
   prouve pas l'absence de donnée inventée, attrape les cas évidents.

4. Qualite du code livré : les fichiers Python **mis en scène** doivent passer
   `ruff check` et `ruff format --check`, chacun sous la configuration de son
   propre projet (`GSIE/API`, `GSIE/SDK/python`, tout projet à venir portant un
   `pyproject.toml`). Le contrôle porte sur les fichiers du commit, jamais sur
   le dépôt entier : on est bloqué par ses propres erreurs, pas par celles d'un
   autre.

   Ajoutée après qu'un commit soit passé avec trois `E501` et trois fichiers
   non formatés. Une porte cassée coûte plus que les lignes qu'elle signale :
   le prochain intervenant ne distingue plus ses erreurs de celles qui
   étaient là, et cesse de la regarder.

   Élargie ensuite : câblée sur `GSIE/API/`, elle laissait passer sans un mot
   l'intégralité du SDK Python né hors de ce chemin. Une porte qui ne couvre
   qu'un dossier donne l'assurance d'une porte sans en avoir la portée.

5. Intégrité des quatre autres familles : la règle 1 ne couvre que
   RFC/DEC/ADR. Les identifiants `GSIE-CON-XXX`, `GSIE-DIR-XXXX`,
   `GSIE-FND-XXX` et `GSIE-PROMPT-XXXX` cités doivent eux aussi pointer vers
   un document existant.

   Ajoutée après mesure du corpus (2026-08-01) : 406 documents,
   3 633 citations, 125 identifiants portés — et `GSIE-CON-005` cité par
   90 documents distincts sans que rien ne vérifie qu'il résolve. L'intégrité
   relevée était de 100 % ; la règle constate cet état plutôt qu'elle ne le
   corrige, et empêche qu'il se dégrade.

   Audit complémentaire du dépôt entier, avec le détail :
   `GSIE/TOOLS/verifier_integrite_references.py`.

Usage : python tools/check_governance_consistency.py
Code de sortie : 0 si rien à signaler, 1 si au moins une violation trouvée.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

# Les formes feminines manquaient : l'accord francais impose « une RFC
# validee », et RFC-0028 comme RFC-0029 emploient cette forme. Le garde-fou
# les tenait donc pour non adoptees, bloquant toute implementation d'une RFC
# pourtant validee et tracee par sa DEC.
#
# Ce n'est pas un assouplissement : « validee » signifie « valide ». Un statut
# « proposee » ou « brouillon » reste refuse, et un test le verifie.
ADOPTED_STATUSES = {
    "validé", "validée", "valide", "validee", "validated",
    "adopté", "adoptée", "adopte", "adoptee", "adopted",
    "accepté", "acceptée", "accepte", "acceptee", "accepted",
    "locked", "verrouillé", "verrouillée", "verrouille", "verrouillee",
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

# --- Règle 5 : les quatre familles d'identifiants que la règle 1 ne voit pas ---
#
# `ID_PATTERN` ne couvre que RFC/DEC/ADR. Les quatre autres familles tracées de
# CLAUDE.md §4 n'étaient vérifiées par rien, alors que `GSIE-CON-005` est
# l'identifiant le plus cité du corpus (87 documents citants) : rien ne
# garantissait qu'il pointe vers un article existant.
#
# Motif et règle séparés de `ID_PATTERN`, délibérément. Ce dernier pilote aussi
# la règle 2 (implémentation avant décision adoptée) : l'élargir aurait rendu
# bloquant tout fichier d'implémentation citant un `GSIE-PROMPT` encore « À
# LANCER ». Une règle qui bloque des commits ne se modifie pas par effet de bord.
FAMILLES_COMPLEMENTAIRES_PATTERN = re.compile(
    r"\b(GSIE-DIR-\d{4}|GSIE-CON-\d{3}|GSIE-FND-\d{3}|GSIE-PROMPT-\d{4})\b"
)

# Élargir le motif sans élargir cette liste signalerait les 770 citations
# constitutionnelles comme brisées : les deux vont ensemble.
REFERENCE_DIRS = [
    "00_CONSTITUTION",
    "01_DIRECTIVES",
    "02_RFC",
    "03_DECISIONS",
    "05_SPECIFICATIONS",
    "GSIE/ARCHITECTURE",
    "GSIE/PROMPTS",
]

# Travail structurant repris en interne, sans délégation à un agent : aucun
# prompt versionné n'a été rédigé, et `GSIE/PROMPTS/REGISTER.md` le déclare
# explicitement en note sous sa table. Les tracer sans fichier est le choix
# documenté, pas un oubli.
#
# L'exemption est nominative, et non un motif « (interne) » générique : un
# futur prompt sans fichier doit rester visible plutôt que d'hériter du
# silence de ceux-ci.
PROMPTS_INTERNES_SANS_FICHIER = frozenset(
    {
        "GSIE-PROMPT-0018",
        "GSIE-PROMPT-0019",
        "GSIE-PROMPT-0020",
        "GSIE-PROMPT-0021",
        "GSIE-PROMPT-0022",
    }
)

GOVERNANCE_DIRS = ["02_RFC", "03_DECISIONS", "GSIE/ARCHITECTURE"]
IMPLEMENTATION_GLOBS = [
    "GSIE/API/alembic/versions/*.py",
    "GSIE/API/src/gsie_api/infrastructure/models/*.py",
    "GSIE/API/src/gsie_api/infrastructure/models.py",
    "GSIE/API/src/gsie_api/infrastructure/knowledge_models.py",
]

# Règle 3 (ADR-009) — moteurs de raisonnement à auditer pour valeurs non sourcées
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

    Best-effort (ADR-009) : repère les blocs `_NOM = ...` (éventuellement
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


# Racine du projet Python : `ruff` doit y etre lance pour que sa configuration
# (`pyproject.toml`) s'applique.
API_ROOT = ROOT / "GSIE" / "API"


def projet_python(chemin: Path) -> Path | None:
    """Racine du projet Python contenant `chemin`, ou `None`.

    C'est le premier ancêtre portant un `pyproject.toml`, sans jamais remonter
    au-dessus du dépôt. Le contrôle était câblé sur `GSIE/API/` : le SDK Python
    (`GSIE/SDK/python/`, autorisé par `RFC-0012` §6) est né hors de ce chemin et
    échappait donc entièrement à la porte de lint — le défaut même que celle-ci
    a été ajoutée pour fermer. Résoudre le projet depuis le fichier plutôt que
    depuis une constante fait que le prochain projet est couvert sans qu'on ait
    à y penser.

    Un fichier sans `pyproject.toml` ancêtre — l'outillage de `tools/` et de
    `GSIE/TOOLS/` — reste hors périmètre : aucune configuration ne dit à quelle
    largeur il doit être formaté, et imposer le défaut de `ruff` reformaterait
    du code aligné à la main. Le silence est ici un choix, pas un oubli.
    """
    for parent in chemin.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
        if parent == ROOT:
            break
    return None


def _fichiers_python_en_scene() -> dict[Path, list[str]]:
    """Fichiers `.py` mis en scène pour ce commit, groupés par projet Python.

    Les chemins sont relatifs à la racine de leur projet, pour que `ruff` les
    reçoive tels qu'il les attend et applique la configuration de ce projet —
    la largeur de ligne du SDK n'est pas celle de l'API. Un fichier supprimé
    est écarté : le linter ne peut rien en dire.
    """
    resultat = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    if resultat.returncode != 0:
        return {}

    par_projet: dict[Path, list[str]] = {}
    for ligne in resultat.stdout.splitlines():
        if not ligne.endswith(".py"):
            continue
        chemin = ROOT / ligne
        projet = projet_python(chemin)
        if projet is None:
            continue
        relatif = chemin.relative_to(projet).as_posix()
        par_projet.setdefault(projet, []).append(relatif)
    return par_projet


def verifier_qualite_python() -> list[str]:
    """Lance `ruff check` et `ruff format --check` sur les fichiers en scène.

    Ne bloque pas si `ruff` est absent : un outil manquant n'est pas une
    incohérence de gouvernance, et empêcher de commiter pour cela punirait
    quiconque n'a pas encore installé l'environnement. Le cas est signalé.
    """
    violations: list[str] = []

    for projet, fichiers in sorted(_fichiers_python_en_scene().items()):
        ruff = projet / ".venv" / "Scripts" / "ruff.exe"
        if not ruff.exists():
            print(
                f"note : {ruff.name} introuvable sous "
                f"{projet.relative_to(ROOT).as_posix()} — contrôle de qualité "
                "Python non exécuté pour ce projet. Installer son environnement "
                "pour l'activer."
            )
            continue

        for arguments, libelle in (
            (["check"], "ruff check"),
            (["format", "--check"], "ruff format"),
        ):
            resultat = subprocess.run(
                [str(ruff), *arguments, *fichiers],
                capture_output=True,
                text=True,
                cwd=projet,
                check=False,
            )
            if resultat.returncode != 0:
                detail = (resultat.stdout + resultat.stderr).strip()
                violations.append(
                    f"[qualité du code] {libelle} échoue sur "
                    f"{len(fichiers)} fichier(s) mis en scène dans "
                    f"{projet.relative_to(ROOT).as_posix()} :\n"
                    + "\n".join(f"      {ligne}" for ligne in detail.splitlines()[:12])
                )
    return violations


def trouver_document_porteur(identifiant: str) -> Path | None:
    """Cherche le fichier portant un identifiant, toutes familles confondues."""
    for base in REFERENCE_DIRS:
        racine = ROOT / base
        if not racine.is_dir():
            continue
        for path in racine.rglob(f"{identifiant}*.md"):
            return path
    return None


def verifier_familles_complementaires() -> list[str]:
    """Règle 5 : `GSIE-CON`/`DIR`/`FND`/`PROMPT` cités doivent exister.

    Mesuré à l'ajout : 408 documents, 3 508 citations, aucune cible manquante
    hors les cinq prompts internes déclarés. La règle constate cet état plutôt
    qu'elle ne le corrige — son objet est d'empêcher qu'il se dégrade.
    """
    violations: list[str] = []

    documents: list[Path] = []
    for base in REFERENCE_DIRS:
        racine = ROOT / base
        if racine.is_dir():
            documents.extend(racine.rglob("*.md"))

    connus: dict[str, bool] = {}
    for path in sorted(documents):
        texte = path.read_text(encoding="utf-8", errors="ignore")
        propres = set(FAMILLES_COMPLEMENTAIRES_PATTERN.findall(path.stem))

        for identifiant in sorted(set(FAMILLES_COMPLEMENTAIRES_PATTERN.findall(texte))):
            if identifiant in propres or identifiant in PROMPTS_INTERNES_SANS_FICHIER:
                continue
            if identifiant not in connus:
                connus[identifiant] = trouver_document_porteur(identifiant) is not None
            if not connus[identifiant]:
                violations.append(
                    f"[réf. cassée] {path.relative_to(ROOT)} référence {identifiant}, "
                    f"introuvable dans {', '.join(REFERENCE_DIRS)} — « aucune "
                    f"décision perdue » (GSIE-CON-005)."
                )
    return violations


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

    # --- Règle 3 (ADR-009) : valeurs numériques potentiellement non sourcées ---
    reasoning_files: list[Path] = []
    for pattern in REASONING_ENGINE_GLOBS:
        reasoning_files.extend(ROOT.glob(pattern))

    for path in reasoning_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in find_unsourced_numeric_constants(text):
            violations.append(
                f"[valeur non sourcée] {path.relative_to(ROOT)} : la constante {name} "
                f"contient un littéral décimal sans citation détectée dans les "
                f"{_CITATION_LOOKBACK_LINES} lignes précédentes (ADR-009) — vérifier "
                f"qu'elle est bien sourcée."
            )

    # --- Règle 5 : intégrité des quatre autres familles d'identifiants ---
    violations.extend(verifier_familles_complementaires())

    violations.extend(verifier_qualite_python())

    if not violations:
        print("OK — aucune incohérence de gouvernance détectée.")
        return 0

    print(f"{len(violations)} incohérence(s) de gouvernance détectée(s) :\n")
    for v in violations:
        print(f"  - {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
