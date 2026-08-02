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
from unittest.mock import patch

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


# ===========================================================================
# Couverture complémentaire — list_species_rich, get_species_image, erreurs
# ===========================================================================


def test_should_raise_error_when_get_species_csv_missing(tmp_path: Path) -> None:
    """get_species doit lever TreekipediaClientError si le CSV est introuvable."""
    client = TreekipediaClient(csv_path=tmp_path / "nonexistent.csv")
    with pytest.raises(TreekipediaClientError, match="CSV Treekipedia introuvable"):
        client.get_species("any-taxon-id")


def test_should_raise_error_when_count_species_csv_missing(tmp_path: Path) -> None:
    """count_species doit lever TreekipediaClientError si le CSV est introuvable."""
    client = TreekipediaClient(csv_path=tmp_path / "nonexistent.csv")
    with pytest.raises(TreekipediaClientError, match="CSV Treekipedia introuvable"):
        client.count_species()


def test_should_raise_error_when_get_species_csv_unreadable(tmp_path: Path) -> None:
    """get_species doit lever TreekipediaClientError si le CSV est illisible."""
    csv_path = tmp_path / "not_a_file_dir"
    csv_path.mkdir()
    client = TreekipediaClient(csv_path=csv_path)
    with pytest.raises(TreekipediaClientError, match="Échec lecture CSV"):
        client.get_species("any-taxon-id")


def test_should_raise_error_when_count_species_csv_unreadable(tmp_path: Path) -> None:
    """count_species doit lever TreekipediaClientError si le CSV est illisible."""
    csv_path = tmp_path / "not_a_file_dir"
    csv_path.mkdir()
    client = TreekipediaClient(csv_path=csv_path)
    with pytest.raises(TreekipediaClientError, match="Échec lecture CSV"):
        client.count_species()


def test_should_list_species_rich_when_csv_exists(tmp_path: Path) -> None:
    """list_species_rich doit lire le CSV riche avec colonnes taxonomiques."""
    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    rich_csv = tmp_path / "treekipedia_species_for_silvi.csv"
    rows = [
        {
            "taxon_id": "GymPiPiPnCx50638-00",
            "species_common_name": "Sapin pectiné",
            "species_scientific_name": "Abies alba",
            "subspecies": "",
            "genus": "Abies",
            "family": "Pinaceae",
            "taxonomic_class": "Pinopsida",
            "taxonomic_order": "Pinales",
        },
        {
            "taxon_id": "AngFaFaCfCx09200-00",
            "species_common_name": "Chêne pédonculé",
            "species_scientific_name": "Quercus robur",
            "subspecies": "",
            "genus": "Quercus",
            "family": "Fagaceae",
            "taxonomic_class": "Magnoliopsida",
            "taxonomic_order": "Fagales",
        },
    ]
    with rich_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "taxon_id",
                "species_common_name",
                "species_scientific_name",
                "subspecies",
                "genus",
                "family",
                "taxonomic_class",
                "taxonomic_order",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with patch.object(tkc_module, "_RICH_CSV_PATH", rich_csv):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        species = client.list_species_rich()
        assert len(species) == 2
        assert species[0]["genus"] == "Abies"


def test_should_filter_species_rich_by_search(tmp_path: Path) -> None:
    """list_species_rich(search=...) doit filtrer par nom scientifique."""
    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    rich_csv = tmp_path / "treekipedia_species_for_silvi.csv"
    rows = [
        {
            "taxon_id": "1",
            "species_common_name": "Sapin",
            "species_scientific_name": "Abies alba",
            "subspecies": "",
            "genus": "Abies",
            "family": "Pinaceae",
            "taxonomic_class": "Pinopsida",
            "taxonomic_order": "Pinales",
        },
        {
            "taxon_id": "2",
            "species_common_name": "Chêne",
            "species_scientific_name": "Quercus robur",
            "subspecies": "",
            "genus": "Quercus",
            "family": "Fagaceae",
            "taxonomic_class": "Magnoliopsida",
            "taxonomic_order": "Fagales",
        },
    ]
    with rich_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "taxon_id",
                "species_common_name",
                "species_scientific_name",
                "subspecies",
                "genus",
                "family",
                "taxonomic_class",
                "taxonomic_order",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with patch.object(tkc_module, "_RICH_CSV_PATH", rich_csv):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        species = client.list_species_rich(search="quercus")
        assert len(species) == 1
        assert species[0]["species_scientific_name"] == "Quercus robur"


def test_should_raise_error_when_rich_csv_missing(tmp_path: Path) -> None:
    """list_species_rich doit lever TreekipediaClientError si le CSV riche est introuvable."""
    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    with patch.object(tkc_module, "_RICH_CSV_PATH", tmp_path / "nonexistent.csv"):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        with pytest.raises(TreekipediaClientError, match="CSV riche Treekipedia introuvable"):
            client.list_species_rich()


def test_should_return_none_when_images_json_missing(tmp_path: Path) -> None:
    """get_species_image doit retourner None si le JSON d'images est introuvable."""
    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    with patch.object(tkc_module, "_IMAGES_JSON_PATH", tmp_path / "nonexistent.json"):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        result = client.get_species_image("Abies alba")
        assert result is None


def test_should_return_image_when_species_found_in_json(tmp_path: Path) -> None:
    """get_species_image doit retourner l'image si l'espèce est dans le JSON."""
    import json

    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    images_json = tmp_path / "treekipedia_images_full.json"
    images = [
        {
            "species": "Abies alba",
            "source": "Wikimedia Commons",
            "image_url": "https://example.com/abies_alba.jpg",
            "license": "CC BY-SA 3.0",
            "photographer": "Test",
            "page_url": "https://commons.wikimedia.org/wiki/Abies_alba",
        }
    ]
    images_json.write_text(json.dumps(images), encoding="utf-8")

    with patch.object(tkc_module, "_IMAGES_JSON_PATH", images_json):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        result = client.get_species_image("Abies alba")
        assert result is not None
        assert result["image_url"] == "https://example.com/abies_alba.jpg"


def test_should_return_none_when_species_not_in_images_json(tmp_path: Path) -> None:
    """get_species_image doit retourner None si l'espèce n'est pas dans le JSON."""
    import json

    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    images_json = tmp_path / "treekipedia_images_full.json"
    images_json.write_text(
        json.dumps([{"species": "Quercus robur", "image_url": "https://example.com/oak.jpg"}]),
        encoding="utf-8",
    )

    with patch.object(tkc_module, "_IMAGES_JSON_PATH", images_json):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        result = client.get_species_image("Abies alba")
        assert result is None


def test_should_match_image_case_insensitive(tmp_path: Path) -> None:
    """get_species_image doit matcher insensiblement à la casse."""
    import json

    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    images_json = tmp_path / "treekipedia_images_full.json"
    images_json.write_text(
        json.dumps([{"species": "Abies Alba", "image_url": "https://example.com/aa.jpg"}]),
        encoding="utf-8",
    )

    with patch.object(tkc_module, "_IMAGES_JSON_PATH", images_json):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        result = client.get_species_image("abies alba")
        assert result is not None


def test_should_raise_error_when_images_json_corrupted(tmp_path: Path) -> None:
    """get_species_image doit lever TreekipediaClientError si le JSON est corrompu."""
    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    images_json = tmp_path / "treekipedia_images_full.json"
    images_json.write_text("<<< not JSON >>>", encoding="utf-8")

    with patch.object(tkc_module, "_IMAGES_JSON_PATH", images_json):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        with pytest.raises(TreekipediaClientError, match="Échec lecture JSON images"):
            client.get_species_image("Abies alba")


# ===========================================================================
# Couverture complémentaire — properties, OSError CSV riche, pagination limit
# ===========================================================================


def test_should_return_correct_exception_class() -> None:
    """exception_class doit retourner TreekipediaClientError."""
    client = TreekipediaClient(csv_path=Path("nonexist.csv"))
    assert client.exception_class is TreekipediaClientError


def test_should_return_correct_base_url() -> None:
    """base_url doit retourner l'URL de l'API Treekipedia."""
    client = TreekipediaClient(csv_path=Path("nonexist.csv"))
    assert client.base_url == "https://treekipedia-api.silvi.earth"


def test_should_raise_error_when_rich_csv_oserror(tmp_path: Path) -> None:
    """list_species_rich doit lever TreekipediaClientError si OSError à la lecture."""
    from unittest.mock import MagicMock

    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    # Mock _RICH_CSV_PATH.exists() → True, mais open lève OSError
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.open.side_effect = OSError("Permission denied")

    with patch.object(tkc_module, "_RICH_CSV_PATH", mock_path):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        with pytest.raises(TreekipediaClientError, match="Échec lecture CSV riche"):
            client.list_species_rich()


def test_should_paginate_with_limit(tmp_path: Path) -> None:
    """list_species_rich doit paginer avec limit."""
    from gsie_api.engines.botanical import treekipedia_client as tkc_module

    csv_content = "species_scientific_name,family\n"
    for i in range(10):
        csv_content += f"Species {i},Family\n"

    rich_csv = tmp_path / "rich.csv"
    rich_csv.write_text(csv_content, encoding="utf-8")

    with patch.object(tkc_module, "_RICH_CSV_PATH", rich_csv):
        client = TreekipediaClient(csv_path=tmp_path / "nonexist.csv")
        result = client.list_species_rich(limit=3)
        assert len(result) == 3
