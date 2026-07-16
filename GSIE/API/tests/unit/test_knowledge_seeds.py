"""Tests des seeds de connaissances (legacy v6.1) — validation des KnowledgeObjects.

Vérifie la cohérence des données de connaissance avant insertion.

NOTE : Les seeds v6.1 seront migrés vers le nouveau schéma v6.2
(Assertion + Concept + Vocabulary) en Vague 2.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="Seeds v6.1 legacy — migration v6.2 (RFC-0012) en Vague 2")

try:
    from gsie_api.seeds.knowledge_data import KNOWLEDGE_OBJECTS
except ImportError:
    KNOWLEDGE_OBJECTS = []  # Module supprimé en v6.2


VALID_TYPES = {"concept", "relation", "regle", "seuil", "modele", "classification"}
VALID_EVIDENCE = {"A", "B", "C", "D", "E", "F"}
VALID_STATUTS = {"accepte", "quarantine", "refuse"}
REQUIRED_FIELDS = {
    "connaissance_id",
    "type",
    "titre",
    "description",
    "domaine_scientifique",
    "contenu",
    "evidence_level",
    "source",
    "statut",
    "version",
    "moteurs_consommateurs",
    "mots_cles",
}


class TestKnowledgeObjectsCount:
    def test_count_above_100(self) -> None:
        assert len(KNOWLEDGE_OBJECTS) >= 100

    def test_ids_unique(self) -> None:
        ids = [k["connaissance_id"] for k in KNOWLEDGE_OBJECTS]
        assert len(ids) == len(set(ids))


class TestKnowledgeObjectsFields:
    def test_all_have_required_fields(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            missing = REQUIRED_FIELDS - set(k.keys())
            assert not missing, (
                f"Connaissance {k.get('connaissance_id', '?')} champs manquants : {missing}"
            )

    def test_type_valid(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            assert k["type"] in VALID_TYPES, (
                f"K {k['connaissance_id']} type invalide : {k['type']}"
            )

    def test_evidence_level_valid(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            assert k["evidence_level"] in VALID_EVIDENCE, (
                f"K {k['connaissance_id']} evidence_level invalide : {k['evidence_level']}"
            )

    def test_statut_valid(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            assert k["statut"] in VALID_STATUTS, (
                f"K {k['connaissance_id']} statut invalide : {k['statut']}"
            )

    def test_version_positive(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            assert k["version"] >= 1

    def test_source_has_reference(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            assert "reference" in k["source"]
            assert isinstance(k["source"]["reference"], str)
            assert len(k["source"]["reference"]) > 0

    def test_mots_cles_not_empty(self) -> None:
        for k in KNOWLEDGE_OBJECTS:
            assert len(k["mots_cles"]) > 0, (
                f"K {k['connaissance_id']} sans mot-clé"
            )


class TestKnowledgeObjectsDiversity:
    def test_multiple_types_present(self) -> None:
        types = {k["type"] for k in KNOWLEDGE_OBJECTS}
        assert "seuil" in types
        assert "relation" in types

    def test_multiple_essences_covered(self) -> None:
        especes: set[str] = set()
        for k in KNOWLEDGE_OBJECTS:
            contenu = k.get("contenu", {})
            if isinstance(contenu, dict) and "espece" in contenu:
                especes.add(contenu["espece"])
        assert len(especes) >= 15, f"Seulement {len(especes)} espèces couvertes"

    def test_multiple_domaines(self) -> None:
        domaines = {k["domaine_scientifique"] for k in KNOWLEDGE_OBJECTS}
        assert len(domaines) >= 3

    def test_classifications_present(self) -> None:
        classifications = [k for k in KNOWLEDGE_OBJECTS if k["type"] == "classification"]
        assert len(classifications) >= 5
