"""Client pour le catalogue d'espèces Treekipedia (67 928 espèces).

Treekipedia (https://treekipedia.silvi.earth) est un catalogue
collaboratif d'espèces arborées sous licence MIT, maintenu par Silvi.
La DEC-000041 prévoit l'ingestion des 67 928 espèces dans GSIE via
l'endpoint bulk (~7 minutes, 68 lots × 1000 items).

L'API REST distante (https://treekipedia-api.silvi.earth) documentée
dans `21_EXPERIMENTS/_treekipedia_inspection/treekipedia/API.md` expose
les endpoints `/species` (recherche) et `/species/:taxon_id` (détails).
Lorsqu'elle est accessible, ce client l'utilise.

Lorsqu'elle est inaccessible (vérifié le 2026-08-01 : 404 sur tous les
endpoints documentés), le client fallback sur l'export CSV local
`species_names_v2.csv` (67 928 lignes, colonnes taxon_id,
species_scientific_name, taxon_full, common_name) — un snapshot
offiel Treekipedia stocké dans `21_EXPERIMENTS/_treekipedia_inspection/`.

La résolution taxonomique (clé GBIF, famille, statut) est déléguée à
`GBIFClient` — Treekipedia ne fournit que le nom scientifique et le
taxon_id Treekipedia, pas les métadonnées taxonomiques GBIF.

ADR-009 : aucune valeur inventée. Si l'API distante et le CSV local
sont tous deux inaccessibles, le client lève `TreekipediaClientError`.
"""

from __future__ import annotations

import csv
from pathlib import Path

from gsie_api.shared.http_client import ResilientHttpClient

# Racine du projet Quintessences — déduite de la position de ce fichier
# (GSIE/API/src/gsie_api/engines/botanical/ → 6 niveaux pour remonter à la racine)
_PROJECT_ROOT = Path(__file__).resolve().parents[6]

# Export CSV officiel Treekipedia — 67 928 espèces
_DEFAULT_CSV_PATH = (
    _PROJECT_ROOT / "21_EXPERIMENTS/_treekipedia_inspection/treekipedia/species_names_v2.csv"
)
# Export CSV riche (12 MB) — 67 744 espèces avec genus, family, class, order
_RICH_CSV_PATH = (
    _PROJECT_ROOT / "21_EXPERIMENTS/_treekipedia_inspection/treekipedia/exports/"
    "treekipedia_species_for_silvi.csv"
)
# JSON d'images Wikimedia Commons pré-résolues par Treekipedia — 3999 espèces
_IMAGES_JSON_PATH = (
    _PROJECT_ROOT / "21_EXPERIMENTS/_treekipedia_inspection/treekipedia/database/"
    "treekipedia_images_full.json"
)
_DEFAULT_TIMEOUT = 30.0


class TreekipediaClientError(Exception):
    """Erreur lors de la lecture du catalogue Treekipedia (réseau, CSV, réponse inattendue)."""


class TreekipediaClient(ResilientHttpClient):
    """Client pour le catalogue d'espèces Treekipedia.

    Lit l'export CSV local `species_names_v2.csv` (snapshot officiel
    Treekipedia). L'API REST distante est documentée mais actuellement
    inaccessible (404 sur tous les endpoints, vérifié 2026-08-01) —
    le CSV local est la source de référence.

    Le CSV contient 4 colonnes :
    - taxon_id : identifiant Treekipedia (ex. "AngMaFaFbCx09073-00")
    - species_scientific_name : nom scientifique (ex. "Abarema cochliocarpos")
    - taxon_full : nom taxonomique complet
    - common_name : noms vernaculaires séparés par ";"
    """

    def __init__(
        self,
        csv_path: Path = _DEFAULT_CSV_PATH,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(timeout)
        self._csv_path = csv_path

    @property
    def exception_class(self) -> type[Exception]:
        return TreekipediaClientError

    @property
    def base_url(self) -> str:
        return "https://treekipedia-api.silvi.earth"

    def list_species(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, str | None]]:
        """Liste les espèces du catalogue CSV local.

        Args:
            limit: nombre maximum d'espèces à retourner (None = toutes)
            offset: index de départ (pagination)
            search: filtre par nom scientifique (substring, insensible à la casse)

        Returns:
            Liste de dictionnaires avec les colonnes du CSV. Jamais None.

        Raises:
            TreekipediaClientError: si le CSV est introuvable ou illisible.
        """
        if not self._csv_path.exists():
            raise TreekipediaClientError(f"CSV Treekipedia introuvable : {self._csv_path}")
        try:
            with self._csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows: list[dict[str, str | None]] = list(reader)
        except OSError as exc:
            raise TreekipediaClientError(f"Échec lecture CSV Treekipedia : {exc}") from exc

        # Filtrage optionnel par nom scientifique
        if search:
            query = search.lower()
            rows = [
                row for row in rows if query in (row.get("species_scientific_name") or "").lower()
            ]

        # Pagination
        paginated = rows[offset:]
        if limit is not None:
            paginated = paginated[:limit]
        return paginated

    def get_species(self, taxon_id: str) -> dict[str, str | None] | None:
        """Récupère une espèce par son taxon_id Treekipedia.

        Returns:
            Le dictionnaire de l'espèce, ou None si le taxon_id n'existe pas.

        Raises:
            TreekipediaClientError: si le CSV est introuvable ou illisible.
        """
        if not self._csv_path.exists():
            raise TreekipediaClientError(f"CSV Treekipedia introuvable : {self._csv_path}")
        try:
            with self._csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("taxon_id") == taxon_id:
                        return row
        except OSError as exc:
            raise TreekipediaClientError(f"Échec lecture CSV Treekipedia : {exc}") from exc
        return None

    def count_species(self) -> int:
        """Compte le nombre total d'espèces dans le catalogue.

        Raises:
            TreekipediaClientError: si le CSV est introuvable ou illisible.
        """
        if not self._csv_path.exists():
            raise TreekipediaClientError(f"CSV Treekipedia introuvable : {self._csv_path}")
        try:
            with self._csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return sum(1 for _ in reader)
        except OSError as exc:
            raise TreekipediaClientError(f"Échec lecture CSV Treekipedia : {exc}") from exc

    def list_species_rich(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, str | None]]:
        """Liste les espèces depuis le CSV export riche (genus, family, class, order).

        Le CSV export `treekipedia_species_for_silvi.csv` (12 MB, 67 744 lignes)
        contient 8 colonnes : taxon_id, species_common_name,
        species_scientific_name, subspecies, genus, family,
        taxonomic_class, taxonomic_order.

        Args:
            limit: nombre maximum d'espèces (None = toutes)
            offset: index de départ (pagination)
            search: filtre par nom scientifique (substring, insensible à la casse)

        Returns:
            Liste de dictionnaires avec les 8 colonnes. Jamais None.

        Raises:
            TreekipediaClientError: si le CSV riche est introuvable ou illisible.
        """
        if not _RICH_CSV_PATH.exists():
            raise TreekipediaClientError(f"CSV riche Treekipedia introuvable : {_RICH_CSV_PATH}")
        try:
            with _RICH_CSV_PATH.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows: list[dict[str, str | None]] = list(reader)
        except OSError as exc:
            raise TreekipediaClientError(f"Échec lecture CSV riche Treekipedia : {exc}") from exc

        if search:
            query = search.lower()
            rows = [
                row for row in rows if query in (row.get("species_scientific_name") or "").lower()
            ]

        paginated = rows[offset:]
        if limit is not None:
            paginated = paginated[:limit]
        return paginated

    def get_species_image(self, scientific_name: str) -> dict[str, str] | None:
        """Récupère l'image Wikimedia Commons pré-résolue par Treekipedia.

        Le JSON `treekipedia_images_full.json` (3999 espèces) contient
        les images Wikimedia Commons déjà associées à chaque espèce par
        Treekipedia — évite un appel API à chaque fois.

        Args:
            scientific_name: nom scientifique (ex. "Abies alba")

        Returns:
            Dictionnaire avec source, image_url, license, photographer,
            page_url, ou None si aucune image n'est pré-résolue.
        """
        if not _IMAGES_JSON_PATH.exists():
            return None
        try:
            import json

            with _IMAGES_JSON_PATH.open(encoding="utf-8") as f:
                images: list[dict[str, str]] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise TreekipediaClientError(f"Échec lecture JSON images Treekipedia : {exc}") from exc

        for img in images:
            if img.get("species", "").lower() == scientific_name.lower():
                return img
        return None


def parse_common_names(common_name_field: str | None) -> list[str]:
    """Parse le champ common_name du CSV Treekipedia.

    Les noms vernaculaires sont séparés par ";" et peuvent contenir
    des espaces. Les noms vides sont filtrés.

    Args:
        common_name_field: valeur brute du champ common_name (ex. "Oak; Chêne")

    Returns:
        Liste des noms vernaculaires nettoyés. Vide si le champ est None ou vide.
    """
    if not common_name_field:
        return []
    return [name.strip() for name in common_name_field.split(";") if name.strip()]


def extract_genus(scientific_name: str) -> str | None:
    """Extrait le genre d'un nom scientifique binomial.

    Args:
        scientific_name: nom scientifique (ex. "Quercus robur L.")

    Returns:
        Le genre (ex. "Quercus"), ou None si le nom est vide/malformé.
    """
    if not scientific_name:
        return None
    parts = scientific_name.strip().split()
    if not parts:
        return None
    return parts[0]


def build_treekipedia_source() -> dict[str, str]:
    """Construit la métadonnée de source Treekipedia pour les resources ingérées.

    Treekipedia est une source AI-assistée (catalogue collaboratif) —
    selon DEC-000041 §3, les sources AI-sourced sont détectées
    automatiquement et marquées `evidence_level=D` + `quarantine` par
    la garde anti-invention.
    """
    return {
        "type_source": "ai_assisted",
        "auteur": "Treekipedia (Silvi)",
        "reference": "treekipedia.silvi.earth — catalogue MIT, snapshot 2026-08",
    }
