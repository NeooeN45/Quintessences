"""Chargeur du dataset réel d'indigénat des espèces arborées (Bellifa et al. 2026).

Source : Bellifa M. et al. (2026), « Indigénat des espèces arborées de
France à l'échelle des sylvoécorégions », Journal de Botanique de la
Société Botanique de France, 124(002). Données déposées sur
Recherche Data Gouv (DOI 10.57745/DHJHGS, licence Etalab Open License
2.0), téléchargées le 2026-07-18 dans
`GSIE/DATASETS/indigenat_especes_arborees_2026/`.

Fichier utilisé : `Synthese_indigenat_SER.tab` (293 taxons × statut
France + 86 sylvoécorégions) — TSV réel, guillemets doubles, en-tête
BOM UTF-8. Aucune valeur n'est réinterprétée au-delà de ce que
`Documentation.txt` (même dataset) définit explicitement (ADR-007).
"""

from __future__ import annotations

import csv
from pathlib import Path

# GSIE/API/src/gsie_api/engines/botanical/indigenat_loader.py -> remonte à GSIE/
_GSIE_DIR = Path(__file__).resolve().parents[5]
DEFAULT_DATASET_PATH = (
    _GSIE_DIR / "DATASETS" / "indigenat_especes_arborees_2026" / "Synthese_indigenat_SER.tab"
)


class IndigenatLoaderError(Exception):
    """Erreur de chargement du dataset d'indigénat (fichier absent ou illisible)."""


class IndigenatLoader:
    """Charge et indexe le dataset TSV réel — aucun appel réseau, fichier local versionné."""

    def __init__(self, dataset_path: Path | None = None) -> None:
        self._dataset_path = dataset_path or DEFAULT_DATASET_PATH
        self._by_cd_nom: dict[int, dict[str, str]] | None = None
        self._by_nom_scientifique: dict[str, dict[str, str]] | None = None
        self._by_binome: dict[str, dict[str, str]] | None = None

    def _ensure_loaded(self) -> None:
        if self._by_cd_nom is not None:
            return

        if not self._dataset_path.exists():
            raise IndigenatLoaderError(
                f"Dataset d'indigénat introuvable : {self._dataset_path} "
                "(DOI 10.57745/DHJHGS, à télécharger séparément)"
            )

        by_cd_nom: dict[int, dict[str, str]] = {}
        by_nom: dict[str, dict[str, str]] = {}
        by_binome: dict[str, dict[str, str]] = {}
        with self._dataset_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t", quotechar='"')
            for row in reader:
                nom_scientifique = row.get("Nom_scientifique", "").strip()
                if not nom_scientifique:
                    continue
                by_nom[nom_scientifique.lower()] = row
                binome = self._extract_binome(nom_scientifique)
                # Premier taxon rencontré gagne en cas de collision binôme
                # (ex. rang subsp. vs espèce) — recherche par cd_nom ou nom
                # complet reste le moyen non ambigu de désambiguïser.
                by_binome.setdefault(binome, row)
                cd_nom_raw = (row.get("CD_NOM_TaxRefv18.0") or "").strip()
                if cd_nom_raw and cd_nom_raw.upper() != "NA":
                    try:
                        by_cd_nom[int(cd_nom_raw)] = row
                    except ValueError:
                        continue

        self._by_cd_nom = by_cd_nom
        self._by_nom_scientifique = by_nom
        self._by_binome = by_binome

    @staticmethod
    def _extract_binome(nom_scientifique: str) -> str:
        """Extrait « genre espèce » en tête du nom complet (avec citation d'auteur)."""
        tokens = nom_scientifique.split()
        return " ".join(tokens[:2]).lower()

    def find(self, cd_nom: int | None, nom_scientifique: str | None) -> dict[str, str] | None:
        """Retrouve la ligne réelle d'un taxon par CD_NOM (priorité) ou nom scientifique.

        La recherche par nom essaie, dans l'ordre : nom complet exact
        (avec citation d'auteur), puis binôme « genre espèce » en tête
        du nom complet (le dataset stocke des noms complets du type
        « Quercus petraea (Matt.) Liebl., 1784 » — une requête avec le
        seul binôme, format le plus courant en usage GSIE, doit
        aboutir).

        Returns:
            None si le taxon n'est présent dans aucune des clés —
            jamais une ligne approximée (ADR-007).
        """
        self._ensure_loaded()
        assert (
            self._by_cd_nom is not None
            and self._by_nom_scientifique is not None
            and self._by_binome is not None
        )

        if cd_nom is not None:
            row = self._by_cd_nom.get(cd_nom)
            if row is not None:
                return row
        if nom_scientifique:
            key = nom_scientifique.strip().lower()
            row = self._by_nom_scientifique.get(key)
            if row is not None:
                return row
            return self._by_binome.get(key)
        return None
