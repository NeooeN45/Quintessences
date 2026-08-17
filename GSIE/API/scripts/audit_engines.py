"""Audit statique minimal des quatorze moteurs GSIE.

Le contrôle est volontairement sans réseau et sans connexion à une base. Il
vérifie le contrat structurel commun avant toute campagne fonctionnelle :
package Python, schémas, routeur, implémentation et montage dans FastAPI.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

MOTEURS: tuple[str, ...] = (
    "evidence",
    "knowledge",
    "gis",
    "climate",
    "pedology",
    "botanical",
    "correlation",
    "forest_dynamics",
    "reasoning",
    "diagnostic",
    "recommendation",
    "validation",
    "simulation",
    "learning",
)


@dataclass(frozen=True)
class ResultatAudit:
    moteur: str
    erreurs: tuple[str, ...]

    @property
    def valide(self) -> bool:
        return not self.erreurs


def auditer_moteurs(racine: Path) -> tuple[ResultatAudit, ...]:
    """Retourne les écarts du contrat structurel des moteurs."""

    engines = racine / "src" / "gsie_api" / "engines"
    app = racine / "src" / "gsie_api" / "app.py"
    contenu_app = app.read_text(encoding="utf-8") if app.is_file() else ""
    resultats: list[ResultatAudit] = []
    for moteur in MOTEURS:
        dossier = engines / moteur
        erreurs: list[str] = []
        for fichier in ("__init__.py", "router.py", "schemas.py"):
            if not (dossier / fichier).is_file():
                erreurs.append(f"fichier manquant: {moteur}/{fichier}")

        # Evidence expose un wrapper contrôlé plutôt qu'un moteur impératif.
        impl = (dossier / "engine.py").is_file() or (
            moteur == "evidence"
            and (dossier / "wrapper.py").is_file()
            and (dossier / "anti_invention.py").is_file()
        )
        if not impl:
            erreurs.append("point d'entrée moteur manquant")

        import_ref = f"from gsie_api.engines.{moteur}.router import router as {moteur}_router"
        include_ref = f"app.include_router({moteur}_router"
        if import_ref not in contenu_app:
            erreurs.append("routeur non importé dans app.py")
        if include_ref not in contenu_app:
            erreurs.append("routeur non monté dans app.py")
        resultats.append(ResultatAudit(moteur, tuple(erreurs)))
    return tuple(resultats)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    resultats = auditer_moteurs(args.root.resolve())
    invalides = [resultat for resultat in resultats if not resultat.valide]
    for resultat in resultats:
        statut = "OK" if resultat.valide else "INVALIDE"
        print(f"{statut} {resultat.moteur}")
        for erreur in resultat.erreurs:
            print(f"  - {erreur}")
    if invalides:
        print(f"AUDIT_MOTEURS=FAIL ({len(invalides)}/{len(resultats)})")
        return 2
    print(f"AUDIT_MOTEURS=OK ({len(resultats)}/{len(resultats)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
