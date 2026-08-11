"""Lecteur du dataset indigenat_especes_arborees_2026 (Bellifa et al. 2026).

Source : Bellifa M. et al., 2026. Indigénat des espèces arborées de
France à l'échelle des sylvoécorégions. Journal de Botanique de la
Société Botanique de France, 124 (002).

Données publiées : 2025. 293 espèces, 86 sylvoécorégions (SER) et
11 grandes régions écologiques (GRECO).

Nomenclature : TAXREF v18.0 (MNHN) ou World Flora Online Plant List.

Codes d'indigénat :
- 1 : indigène
- 2 : probablement indigène
- 3 : probablement exogène
- 9 : cryptogène
- 0 : exogène ou absent
- 0 - A : exogène archéophyte (échelle France)
- 0 - N : exogène néophyte (échelle France)

Ce module fournit un accès programmatique aux données d'indigénat pour
enrichir le ground truth des scénarios de validation (DEC-000043 S3).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent

# Codes GRECO (grandes régions écologiques françaises)
GRECO_CODES = list("ABCDEFGHIJK")


class StatutIndigenat(str, Enum):
    """Statut d'indigénat à l'échelle France."""

    INDIGENE = "1"
    EXOGENE_ARCHEOPHYTE = "0 - A"
    EXOGENE_NEOPHYTE = "0 - N"
    CRYPTOGENE = "9"


@dataclass(frozen=True)
class EspeceArboree:
    """Une espèce arborée et son indigénat par GRECO."""

    nom_scientifique: str
    nom_vernaculaire: str
    cd_nom_taxref: str
    famille: str
    synonyme: str
    indigenat_fr: str
    indigenat_greco: dict[str, str]  # code GRECO → statut

    @property
    def est_indigene_fr(self) -> bool:
        """Indigène à l'échelle de la France hexagonale."""
        return self.indigenat_fr == StatutIndigenat.INDIGENE.value

    @property
    def est_exogene(self) -> bool:
        """Exogène (archéophyte ou néophyte)."""
        return self.indigenat_fr.startswith("0")

    def est_indigene_dans(self, code_greco: str) -> bool:
        """Indigène ou probablement indigène dans une GRECO donnée."""
        statut = self.indigenat_greco.get(code_greco.upper(), "0")
        return statut in ("1", "2")

    @property
    def grecos_indigene(self) -> list[str]:
        """Liste des GRECOs où l'espèce est indigène."""
        return [k for k, v in self.indigenat_greco.items() if v in ("1", "2")]


def _load_greco() -> list[EspeceArboree]:
    """Charge les données d'indigénat par GRECO."""
    filepath = DATASET_DIR / "Synthese_indigenat_GRECO.tab"
    with filepath.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        especes = []
        for row in reader:
            indigenat_greco = {code: row.get(code, "0") for code in GRECO_CODES}
            especes.append(
                EspeceArboree(
                    nom_scientifique=row["Nom_scientifique"],
                    nom_vernaculaire=row["Nom_vernaculaire"],
                    cd_nom_taxref=row.get("CD_NOM_TaxRefv18.0", "NA"),
                    famille=row.get("Famille", ""),
                    synonyme=row.get("Synonyme", ""),
                    indigenat_fr=row.get("Indigenat FR", "0"),
                    indigenat_greco=indigenat_greco,
                )
            )
        return especes


_ESPECES_CACHE: list[EspeceArboree] | None = None


def all_especes() -> list[EspeceArboree]:
    """Retourne toutes les espèces du dataset (cache en mémoire)."""
    global _ESPECES_CACHE
    if _ESPECES_CACHE is None:
        _ESPECES_CACHE = _load_greco()
    return _ESPECES_CACHE


def find_espece(nom_scientifique: str) -> EspeceArboree | None:
    """Trouve une espèce par nom scientifique (insensible à la casse)."""
    nom_lower = nom_scientifique.lower()
    for esp in all_especes():
        if esp.nom_scientifique.lower() == nom_lower:
            return esp
    # Recherche par préfixe (ex: "Quercus robur" matche "Quercus robur L., 1753")
    for esp in all_especes():
        if esp.nom_scientifique.lower().startswith(nom_lower):
            return esp
    return None


def especes_indigenes_dans_greco(code_greco: str) -> list[EspeceArboree]:
    """Espèces indigènes dans une GRECO donnée."""
    return [esp for esp in all_especes() if esp.est_indigene_dans(code_greco)]


def especes_exogenes() -> list[EspeceArboree]:
    """Espèces exogènes (non indigènes à l'échelle France)."""
    return [esp for esp in all_especes() if esp.est_exogene]
