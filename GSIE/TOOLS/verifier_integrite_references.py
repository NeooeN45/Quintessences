#!/usr/bin/env python3
"""Audit d'intégrité référentielle du corpus documentaire Quintessences.

Chaque identifiant tracé (`CLAUDE.md` §4) cité dans un document doit pointer
vers un document qui le porte. Une citation sans cible est une décision perdue —
ce que `GSIE-CON-005` interdit.

**Complémentaire du garde-fou, pas redondant.** La règle 5 de
`tools/check_governance_consistency.py` bloque au commit et se limite aux
dossiers de gouvernance. Cet outil-ci audite le dépôt entier et rend le détail :
volumétrie, familles, identifiants les plus cités, citations orphelines. Il sert
à constater l'état du corpus, pas à barrer un commit.

Mesure de référence au 2026-08-01 : 406 documents, 125 identifiants portés,
3 633 citations, **aucune cible manquante** hors les cinq prompts internes que
`GSIE/PROMPTS/REGISTER.md` déclare explicitement sans fichier. C'est un
instantané daté, pas un invariant : le corpus grossit, et seule la dernière
ligne — l'absence de cible manquante — est la propriété que cet outil garantit.

`plus_cites` compte les **documents citants**, jamais les occurrences : deux
mentions dans un même fichier restent une seule arête. Les deux grandeurs
diffèrent d'un tiers sur ce corpus — les confondre fausse toute lecture.

Usage :
    python GSIE/TOOLS/verifier_integrite_references.py [racine] [--json]

Code de sortie : 0 si l'intégrité est complète, 1 sinon.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Dépôts git indépendants (`CLAUDE.md` §10) et outillage : hors périmètre de
# gouvernance du dépôt parent, qui les ignore déjà.
#
# Les caches d'outils y figurent parce qu'ils déposent leur propre `README.md` :
# lancer la suite de tests du SDK faisait entrer `.pytest_cache/README.md` dans
# le corpus et montait le compte de documents d'une unité. Une mesure qui bouge
# selon qu'on vient ou non de lancer les tests ne mesure pas le corpus.
EXCLUS = {
    ".git",
    ".venv",
    "node_modules",
    ".claude",
    "Forge",
    "apps",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}

FAMILLES = {
    "RFC": re.compile(r"\bRFC-(\d{4})\b"),
    "DEC": re.compile(r"\bDEC-(\d{6})\b"),
    "GSIE-DIR": re.compile(r"\bGSIE-DIR-(\d{4})\b"),
    "GSIE-CON": re.compile(r"\bGSIE-CON-(\d{3})\b"),
    "GSIE-FND": re.compile(r"\bGSIE-FND-(\d{3})\b"),
    "ADR": re.compile(r"\bADR-(\d{3,4})(?!\d)"),
    "GSIE-PROMPT": re.compile(r"\bGSIE-PROMPT-(\d{4})\b"),
}

# Travail structurant repris en interne, sans délégation : aucun prompt versionné
# n'a été rédigé au préalable, et `GSIE/PROMPTS/REGISTER.md` le déclare en note
# sous sa table. Les tracer sans fichier est le choix documenté, pas un oubli.
#
# Nominative et non générique : un futur prompt sans fichier doit rester visible
# plutôt que d'hériter du silence de ceux-ci.
PROMPTS_INTERNES_SANS_FICHIER = frozenset(
    {
        "GSIE-PROMPT-0018",
        "GSIE-PROMPT-0019",
        "GSIE-PROMPT-0020",
        "GSIE-PROMPT-0021",
        "GSIE-PROMPT-0022",
    }
)

# Un identifiant cité sur une ligne qui le déclare absent — différé, remplacé,
# à créer — n'est pas une référence brisée mais une intention tracée. C'est le
# cas des ADR-0008 à 0013, retirés avant rédaction et marqués « (différé) ».
DECLARE_ABSENT = re.compile(
    r"différ|differ|remplac|supersed|obsol|planifi|à créer|a creer|futur|abandonn|absen|non attribu|non document",
    re.IGNORECASE,
)

# Un ADR peut être porté par une section d'un registre plutôt que par un fichier
# dédié. La forme est volontairement stricte : un titre « Compatibilité avec
# ADR-099 » reste une citation, tandis que « ## ADR-099 — Décision » ou une
# ligne de métadonnée `**ID**` constitue une définition.
ADR_INTERNE = re.compile(
    r"(?:^#{1,6}\s+(?:\d+(?:\.\d+)*\.?\s+)?(ADR-\d{3,4})\s+[—-])"
    r"|(?:^\s*\|\s*\*\*ID\*\*\s*\|\s*(ADR-\d{3,4})\s*\|)",
    re.MULTILINE,
)


def documents(racine: Path) -> list[Path]:
    """Markdown du corpus, dépôts imbriqués exclus.

    Un dossier qui porte son propre `.git` est un dépôt indépendant
    (`CLAUDE.md` §10) : ses documents ne sont pas ceux de Quintessences et
    leurs identifiants n'ont pas à résoudre ici. Le clone d'inspection
    Treekipedia sous `21_EXPERIMENTS/` en ajoutait 149 au corpus et aurait
    signalé comme brisée toute citation d'un identifiant étranger.

    La frontière se détecte par la présence de `.git`, non par le nom du
    dossier : `EXCLUS` ne cite que les dépôts déjà connus de `CLAUDE.md` §10,
    et devrait être révisé à chaque nouveau clone déposé. Une liste qu'il faut
    penser à tenir à jour est une liste qui finira périmée.
    """
    trouves: list[Path] = []
    for dossier, sous_dossiers, fichiers in os.walk(racine):
        courant = Path(dossier)
        # Élagage en place : `os.walk` ne descend pas dans ce qu'on retire ici.
        sous_dossiers[:] = [
            d
            for d in sous_dossiers
            if d not in EXCLUS and not (courant / d / ".git").exists()
        ]
        trouves.extend(courant / f for f in fichiers if f.endswith(".md"))
    # Ordre stable : `os.walk` dépend du système de fichiers, et le rapport
    # doit être comparable d'une machine à l'autre.
    return sorted(trouves)


def auditer(racine: Path) -> dict[str, object]:
    corpus = documents(racine)

    # Un identifiant est *porté* si un nom de fichier le contient.
    portes: dict[str, str] = {}
    for chemin in corpus:
        for famille, motif in FAMILLES.items():
            for numero in motif.findall(chemin.name):
                portes.setdefault(
                    f"{famille}-{numero}",
                    str(chemin.relative_to(racine)).replace("\\", "/"),
                )

    # Deuxième passe : définitions internes de registres ADR. La première passe
    # reste fondée sur les noms de fichiers pour toutes les autres familles.
    for chemin in corpus:
        try:
            texte = chemin.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        relatif = str(chemin.relative_to(racine)).replace("\\", "/")
        for groupes in ADR_INTERNE.findall(texte):
            identifiant = groupes[0] or groupes[1]
            portes.setdefault(identifiant, relatif)

    # Un registre de supersession vaut résolution globale, pas seulement sur la
    # ligne où il est énoncé. Sans cette passe, les anciens ADR-0008..0013 sont
    # à nouveau signalés dans leur décision d'origine alors qu'une DEC ultérieure
    # trace explicitement leur remplacement par ADR-001..006.
    declares_absents: set[str] = set()
    for chemin in corpus:
        try:
            lignes = chemin.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for ligne in lignes:
            if not DECLARE_ABSENT.search(ligne):
                continue
            for famille, motif in FAMILLES.items():
                declares_absents.update(
                    f"{famille}-{numero}" for numero in motif.findall(ligne)
                )

    brisees: list[dict[str, object]] = []
    citations: Counter[str] = Counter()
    entrants: Counter[str] = Counter()

    for chemin in corpus:
        relatif = str(chemin.relative_to(racine)).replace("\\", "/")
        try:
            lignes = chemin.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        # `entrants` compte les documents citants, pas les occurrences : deux
        # mentions dans un même fichier restent une seule arête du graphe. Les
        # confondre gonfle les identifiants cités en boucle dans un long
        # document et fausse la lecture du centre de gravité.
        deja_comptes: set[str] = set()

        for numero_ligne, ligne in enumerate(lignes, 1):
            for famille, motif in FAMILLES.items():
                for numero in motif.findall(ligne):
                    identifiant = f"{famille}-{numero}"
                    citations[famille] += 1
                    if identifiant in portes:
                        if (
                            portes[identifiant] != relatif
                            and identifiant not in deja_comptes
                        ):
                            deja_comptes.add(identifiant)
                            entrants[identifiant] += 1
                        continue
                    if identifiant in PROMPTS_INTERNES_SANS_FICHIER:
                        continue
                    if identifiant in declares_absents:
                        continue
                    if DECLARE_ABSENT.search(ligne):
                        continue
                    brisees.append(
                        {
                            "identifiant": identifiant,
                            "fichier": relatif,
                            "ligne": numero_ligne,
                            "extrait": ligne.strip()[:120],
                        }
                    )

    return {
        "documents": len(corpus),
        "identifiants_portes": len(portes),
        "citations_par_famille": dict(citations),
        "citations_total": sum(citations.values()),
        "plus_cites": entrants.most_common(10),
        "brisees": brisees,
    }


def main() -> int:
    arguments = [a for a in sys.argv[1:] if a != "--json"]
    racine = Path(arguments[0] if arguments else ".").resolve()
    rapport = auditer(racine)

    if "--json" in sys.argv[1:]:
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
        return 1 if rapport["brisees"] else 0

    brisees = rapport["brisees"]
    assert isinstance(brisees, list)

    print(f"Corpus       : {rapport['documents']} documents Markdown")
    print(f"Identifiants : {rapport['identifiants_portes']} portés par un document")
    print(f"Citations    : {rapport['citations_total']}")
    print()
    print("Identifiants les plus cités — en nombre de documents citants :")
    plus_cites = rapport["plus_cites"]
    assert isinstance(plus_cites, list)
    for identifiant, nombre in plus_cites:
        print(f"  {nombre:4d}  {identifiant}")
    print()

    if not brisees:
        total = rapport["citations_total"]
        print(f"Intégrité complète : {total} citations, aucune cible manquante.")
        return 0

    print(f"{len(brisees)} référence(s) brisée(s) :")
    for reference in brisees:
        print(
            f"  - {reference['fichier']}:{reference['ligne']} → {reference['identifiant']}"
        )
        print(f"      {reference['extrait']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
