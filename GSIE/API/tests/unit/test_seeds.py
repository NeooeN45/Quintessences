"""Tests des seeds (legacy v6.1) — validation des données de référence.

Vérifie la cohérence des données botaniques et écosystémiques
avant insertion en base. Pas de DB requise — tests sur les constantes.

NOTE : Les seeds v6.1 (botanical_data, ecosystem_data) seront migrés
vers le nouveau schéma v6.2 (Concept + Vocabulary + ControlledTerm)
en Vague 2.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="Seeds v6.1 legacy — migration v6.2 (RFC-0012) en Vague 2")

try:
    from gsie_api.seeds.botanical_data import ESSENCES, FAMILLES, GENRES
    from gsie_api.seeds.ecosystem_data import (
        GROUPES_ECOLOGIQUES,
        HABITATS_NATURA2000,
        STATIONS_FORESTIERES,
    )
except ImportError:
    ESSENCES, FAMILLES, GENRES = [], [], []
    GROUPES_ECOLOGIQUES, HABITATS_NATURA2000, STATIONS_FORESTIERES = [], [], []


# --- Tests botaniques ---


class TestBotanicalFamilles:
    def test_familles_count(self) -> None:
        assert len(FAMILLES) >= 20

    def test_familles_unique(self) -> None:
        noms = [f["nom_scientifique"] for f in FAMILLES]
        assert len(noms) == len(set(noms))

    def test_familles_have_required_fields(self) -> None:
        for f in FAMILLES:
            assert "nom_scientifique" in f
            assert "source_reference" in f
            assert isinstance(f["nom_scientifique"], str)
            assert isinstance(f["source_reference"], str)


class TestBotanicalGenres:
    def test_genres_count(self) -> None:
        assert len(GENRES) >= 30

    def test_genres_unique(self) -> None:
        noms = [g["nom_scientifique"] for g in GENRES]
        assert len(noms) == len(set(noms))

    def test_genres_have_required_fields(self) -> None:
        for g in GENRES:
            assert "nom_scientifique" in g
            assert "famille_nom" in g
            assert "source_reference" in g

    def test_genres_famille_exists(self) -> None:
        famille_noms = {f["nom_scientifique"] for f in FAMILLES}
        for g in GENRES:
            nom = g["nom_scientifique"]
            famille = g["famille_nom"]
            assert (
                famille in famille_noms
            ), f"Genre {nom} référence une famille inexistante : {famille}"


class TestBotanicalEssences:
    def test_essences_count(self) -> None:
        assert len(ESSENCES) >= 50

    def test_essences_unique(self) -> None:
        noms = [e["nom_scientifique"] for e in ESSENCES]
        assert len(noms) == len(set(noms))

    def test_essences_have_required_fields(self) -> None:
        for e in ESSENCES:
            assert "nom_scientifique" in e
            assert "nom_vernaculaire" in e
            assert "genre_nom" in e
            assert "categorie_forestiere" in e
            assert "source_reference" in e

    def test_essences_genre_exists(self) -> None:
        genre_noms = {g["nom_scientifique"] for g in GENRES}
        for e in ESSENCES:
            assert (
                e["genre_nom"] in genre_noms
            ), f"Essence {e['nom_scientifique']} référence un genre inexistant : {e['genre_nom']}"

    @pytest.mark.parametrize(
        "categorie",
        [
            "feuillu_principal",
            "feuillu_accompagnement",
            "conifere_principal",
            "conifere_accompagnement",
            "pionniere",
        ],
    )
    def test_essences_categorie_valid(self, categorie: str) -> None:
        categories = {e["categorie_forestiere"] for e in ESSENCES}
        assert categorie in categories

    def test_essences_have_feuillus_principaux(self) -> None:
        principaux = [e for e in ESSENCES if e["categorie_forestiere"] == "feuillu_principal"]
        assert len(principaux) >= 10

    def test_essences_have_coniferes_principaux(self) -> None:
        principaux = [e for e in ESSENCES if e["categorie_forestiere"] == "conifere_principal"]
        assert len(principaux) >= 8

    def test_essences_includes_key_species(self) -> None:
        noms_scientifiques = {e["nom_scientifique"] for e in ESSENCES}
        expected = {
            "Quercus petraea",
            "Quercus robur",
            "Fagus sylvatica",
            "Pinus sylvestris",
            "Picea abies",
            "Abies alba",
            "Pseudotsuga menziesii",
            "Carpinus betulus",
            "Fraxinus excelsior",
        }
        missing = expected - noms_scientifiques
        assert not missing, f"Essences manquantes : {missing}"


# --- Tests écosystèmes ---


class TestHabitatsNatura2000:
    def test_habitats_count(self) -> None:
        assert len(HABITATS_NATURA2000) >= 20

    def test_habitats_unique(self) -> None:
        codes = [h["code_eur28"] for h in HABITATS_NATURA2000]
        assert len(codes) == len(set(codes))

    def test_habitats_have_required_fields(self) -> None:
        for h in HABITATS_NATURA2000:
            assert "code_eur28" in h
            assert "nom_habitat" in h
            assert "description" in h
            assert "categorie" in h
            assert "source_reference" in h

    def test_habitats_include_priority(self) -> None:
        priority = [h for h in HABITATS_NATURA2000 if h.get("interet_patrimonial") == "prioritaire"]
        assert len(priority) >= 1

    def test_habitats_categories_valid(self) -> None:
        valid_categories = {"Forêts", "Landes", "Pelouses", "Tourbières", "Prairies", "Buissons"}
        for h in HABITATS_NATURA2000:
            assert (
                h["categorie"] in valid_categories
            ), f"Habitat {h['code_eur28']} catégorie invalide : {h['categorie']}"


class TestStationsForestieres:
    def test_stations_count(self) -> None:
        assert len(STATIONS_FORESTIERES) >= 10

    def test_stations_unique(self) -> None:
        codes = [s["code_station"] for s in STATIONS_FORESTIERES]
        assert len(codes) == len(set(codes))

    def test_stations_have_required_fields(self) -> None:
        for s in STATIONS_FORESTIERES:
            assert "code_station" in s
            assert "nom_station" in s
            assert "description" in s
            assert "essences_adaptees" in s
            assert "source_reference" in s

    def test_stations_have_essences(self) -> None:
        for s in STATIONS_FORESTIERES:
            assert (
                len(s["essences_adaptees"]) > 0
            ), f"Station {s['code_station']} sans essence adaptée"


class TestGroupesEcologiques:
    def test_groupes_count(self) -> None:
        assert len(GROUPES_ECOLOGIQUES) >= 10

    def test_groupes_unique(self) -> None:
        noms = [g["nom_groupe"] for g in GROUPES_ECOLOGIQUES]
        assert len(noms) == len(set(noms))

    def test_groupes_have_required_fields(self) -> None:
        for g in GROUPES_ECOLOGIQUES:
            assert "nom_groupe" in g
            assert "description" in g
            assert "indicateur" in g
            assert "especes_caracteristiques" in g
            assert "source_reference" in g

    def test_groupes_have_especes(self) -> None:
        for g in GROUPES_ECOLOGIQUES:
            assert (
                len(g["especes_caracteristiques"]) >= 3
            ), f"Groupe {g['nom_groupe']} avec trop peu d'espèces"

    def test_groupes_indicateurs_diverse(self) -> None:
        indicateurs = {g["indicateur"] for g in GROUPES_ECOLOGIQUES}
        assert len(indicateurs) >= 4, f"Indicateurs insuffisamment diversifiés : {indicateurs}"
