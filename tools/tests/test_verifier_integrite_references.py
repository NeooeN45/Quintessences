"""Tests de l'auditeur d'intégrité référentielle documentaire."""

from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "GSIE"
    / "TOOLS"
    / "verifier_integrite_references.py"
)
SPEC = importlib.util.spec_from_file_location(
    "verifier_integrite_references", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_adr_defini_dans_un_registre_interne_resout_les_citations(tmp_path):
    architecture = tmp_path / "GSIE" / "ARCHITECTURE"
    architecture.mkdir(parents=True)
    (architecture / "REGISTRE_ADR.md").write_text(
        "# Registre\n\n## ADR-042 — Choix interne\n\nDécision.\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "Le composant applique ADR-042.\n", encoding="utf-8"
    )

    rapport = MODULE.auditer(tmp_path)

    assert rapport["brisees"] == []


def test_simple_citation_adr_dans_un_titre_ne_devient_pas_definition(tmp_path):
    (tmp_path / "README.md").write_text(
        "## Compatibilité avec ADR-099\n", encoding="utf-8"
    )

    rapport = MODULE.auditer(tmp_path)

    assert [item["identifiant"] for item in rapport["brisees"]] == ["ADR-099"]


def test_adr_historique_a_quatre_chiffres_defini_en_interne_est_reconnu(tmp_path):
    (tmp_path / "TECHNOLOGY_STACK.md").write_text(
        "## 3. ADR-0001 — Python\n\n| **ID** | ADR-0001 |\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("Voir ADR-0001.\n", encoding="utf-8")

    rapport = MODULE.auditer(tmp_path)

    assert rapport["brisees"] == []


def test_adr_remplace_est_resolu_dans_tout_le_corpus(tmp_path):
    (tmp_path / "DECISION_INITIALE.md").write_text(
        "| Choix | ADR-0008 |\n", encoding="utf-8"
    )
    (tmp_path / "REGISTRE.md").write_text(
        "ADR-0008 remplacé par ADR-001.\n" "## ADR-001 — Choix définitif\n",
        encoding="utf-8",
    )

    rapport = MODULE.auditer(tmp_path)

    assert rapport["brisees"] == []


def test_identifiant_explicitement_absent_ne_devient_pas_reference_brisee(tmp_path):
    (tmp_path / "AUDIT.md").write_text(
        "GSIE-DIR-0002 absent et non documenté comme réservé.\n",
        encoding="utf-8",
    )

    rapport = MODULE.auditer(tmp_path)

    assert rapport["brisees"] == []
