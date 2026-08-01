"""Tests unitaires — TreekipediaClient (lecture CSV local).

Le client Treekipedia lit l'export CSV officiel (67 928 espèces).
Ces tests vérifient :
- la lecture du CSV (list, get, count)
- le filtrage par nom scientifique
- la pagination (limit + offset)
- la robustesse aux fichiers manquants ou illisibles
- les helpers (parse_common_names, extract_genus, build_treekipedia_source)

Contrairement aux autres clients (GBIF, IGN, etc.), TreekipediaClient
lit un fichier local — les tests paramétrés du factory réseau
(test_resilience_factory.py) ne s'appliquent pas.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from gsie_api.engines.botanical.treekipedia_client import (
    TreekipediaClient,
    TreekipediaClientError,
    build_treekipedia_source,
    extract_genus,
    parse_common_names,
)

# --- Fixtures ---


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Crée un CSV Treekipedia temporaire avec 5 espèces de test."""
    csv_path = tmp_path / "test_species.csv"
    rows = [
        {
            "taxon_id": "AngMaFaFbCx09073-00",
            "species_scientific_name": "Abarema cochliocarpos",
            "taxon_full": "Abarema cochliocarpos",
            "common_name": "Barbatimão; Saboeiro",
        },
        {
            "taxon_id": "GymPiPiPnCx50638-00",
            "species_scientific_name": "Abies alba",
            "taxon_full": "Abies alba Mill.",
            "common_name": "Sapin pectiné; Silver fir",
        },
        {
            "taxon_id": "GymPiPiPnCx50639-00",
            "species_scientific_name": "Abies amabilis",
            "taxon_full": "Abies amabilis Dougl.",
            "common_name": "Pacific silver fir",
        },
        {
            "taxon_id": "AngFaFaCfCx09200-00",
            "species_scientific_name": "Quercus robur",
            "taxon_full": "Quercus robur L.",
            "common_name": "Chêne pédonculé; English oak; Pedunculate oak",
        },
        {
            "taxon_id": "AngFaFaCfCx09201-00",
            "species_scientific_name": "Quercus petraea",
            "taxon_full": "Quercus petraea Liebl.",
            "common_name": "",
        },
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["taxon_id", "species_scientific_name", "taxon_full", "common_name"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


@pytest.fixture
def client(sample_csv: Path) -> TreekipediaClient:
    """Client Treekipedia pointant vers le CSV de test."""
    return TreekipediaClient(csv_path=sample_csv)


# --- Tests list_species ---


def test_should_list_all_species_when_no_limit(client: TreekipediaClient) -> None:
    """list_species() sans limit retourne toutes les espèces du CSV."""
    species = client.list_species()
    assert len(species) == 5
    assert species[0]["species_scientific_name"] == "Abarema cochliocarpos"


def test_should_limit_results_when_limit_provided(client: TreekipediaClient) -> None:
    """list_species(limit=2) retourne exactement 2 espèces."""
    species = client.list_species(limit=2)
    assert len(species) == 2


def test_should_offset_results_when_offset_provided(client: TreekipediaClient) -> None:
    """list_species(offset=2) saute les 2 premières espèces."""
    species = client.list_species(offset=2)
    assert len(species) == 3
    assert species[0]["species_scientific_name"] == "Abies amabilis"


def test_should_filter_by_scientific_name_when_search_provided(
    client: TreekipediaClient,
) -> None:
    """list_species(search='Quercus') filtre par nom scientifique (insensible à la casse)."""
    species = client.list_species(search="quercus")
    assert len(species) == 2
    assert all("quercus" in s["species_scientific_name"].lower() for s in species)


def test_should_return_empty_list_when_search_matches_nothing(
    client: TreekipediaClient,
) -> None:
    """list_species(search='NonExistent') retourne une liste vide."""
    species = client.list_species(search="NonExistentSpecies")
    assert species == []


# --- Tests get_species ---


def test_should_return_species_when_taxon_id_exists(
    client: TreekipediaClient,
) -> None:
    """get_species() retourne l'espèce si le taxon_id existe."""
    species = client.get_species("GymPiPiPnCx50638-00")
    assert species is not None
    assert species["species_scientific_name"] == "Abies alba"


def test_should_return_none_when_taxon_id_not_found(
    client: TreekipediaClient,
) -> None:
    """get_species() retourne None si le taxon_id n'existe pas."""
    species = client.get_species("NonExistent-00")
    assert species is None


# --- Tests count_species ---


def test_should_count_all_species(client: TreekipediaClient) -> None:
    """count_species() retourne le nombre total de lignes."""
    assert client.count_species() == 5


# --- Tests robustesse ---


def test_should_raise_error_when_csv_file_missing(tmp_path: Path) -> None:
    """Une erreur est levée si le CSV n'existe pas."""
    client = TreekipediaClient(csv_path=tmp_path / "nonexistent.csv")
    with pytest.raises(TreekipediaClientError, match="CSV Treekipedia introuvable"):
        client.list_species()


def test_should_raise_error_when_csv_unreadable(tmp_path: Path) -> None:
    """Une erreur est levée si le CSV est un répertoire (illisible comme fichier).

    Note : chmod(0o000) n'est pas portable sur Windows (l'admin peut
    toujours lire) — on utilise un répertoire à la place pour garantir
    l'échec de open() sur tous les OS.
    """
    csv_path = tmp_path / "not_a_file_dir"
    csv_path.mkdir()
    client = TreekipediaClient(csv_path=csv_path)
    with pytest.raises(TreekipediaClientError, match="Échec lecture CSV"):
        client.list_species()


def test_should_return_empty_list_when_csv_has_only_header(
    tmp_path: Path,
) -> None:
    """Un CSV avec seulement l'en-tête retourne une liste vide."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text(
        "taxon_id,species_scientific_name,taxon_full,common_name\n",
        encoding="utf-8",
    )
    client = TreekipediaClient(csv_path=csv_path)
    assert client.list_species() == []
    assert client.count_species() == 0


# --- Tests helpers ---


def test_should_parse_common_names_separated_by_semicolon() -> None:
    """parse_common_names() sépare par ';' et nettoie les espaces."""
    names = parse_common_names("Chêne pédonculé; English oak; Pedunculate oak")
    assert names == ["Chêne pédonculé", "English oak", "Pedunculate oak"]


def test_should_return_empty_list_when_common_name_is_none() -> None:
    """parse_common_names(None) retourne une liste vide."""
    assert parse_common_names(None) == []


def test_should_return_empty_list_when_common_name_is_empty() -> None:
    """parse_common_names('') retourne une liste vide."""
    assert parse_common_names("") == []


def test_should_filter_empty_names_in_common_name_field() -> None:
    """parse_common_names() filtre les noms vides entre '; ;'."""
    names = parse_common_names("Oak; ; Pine;  ; ")
    assert names == ["Oak", "Pine"]


def test_should_extract_genus_from_binomial_name() -> None:
    """extract_genus() retourne le premier mot du nom scientifique."""
    assert extract_genus("Quercus robur L.") == "Quercus"


def test_should_return_none_when_scientific_name_is_empty() -> None:
    """extract_genus('') retourne None."""
    assert extract_genus("") is None


def test_should_return_none_when_scientific_name_is_only_spaces() -> None:
    """extract_genus('   ') retourne None."""
    assert extract_genus("   ") is None


def test_should_build_treekipedia_source_with_ai_assisted_type() -> None:
    """build_treekipedia_source() marque la source comme ai_assisted (DEC-000041 §3)."""
    source = build_treekipedia_source()
    assert source["type_source"] == "ai_assisted"
    assert "Treekipedia" in source["auteur"]
    assert "silvi.earth" in source["reference"]


# --- Test d'intégration avec le CSV réel (si présent) ---


def test_should_read_real_treekipedia_csv_when_present() -> None:
    """Test d'intégration : lit les 5 premières lignes du CSV réel Treekipedia.

    Ignoré si le CSV réel n'est pas présent (environnement sans le dépôt
    d'inspection Treekipedia).
    """
    real_csv = Path(
        "A:/Quintessences/21_EXPERIMENTS/_treekipedia_inspection/treekipedia/species_names_v2.csv"
    )
    if not real_csv.exists():
        pytest.skip("CSV réel Treekipedia non disponible")
    client = TreekipediaClient(csv_path=real_csv)
    species = client.list_species(limit=5)
    assert len(species) == 5
    assert all(s.get("taxon_id") for s in species)
    assert all(s.get("species_scientific_name") for s in species)
