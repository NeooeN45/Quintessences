"""Tests du garde-fou de cohérence de gouvernance.

Couvre la résolution du projet Python d'un fichier — le point sur lequel la
règle 4 (qualité du code livré) décide quelle configuration `ruff` appliquer,
et donc si un fichier est contrôlé ou ignoré en silence.
"""

from __future__ import annotations

import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import tools.check_governance_consistency as garde


@contextmanager
def depot_temporaire() -> Iterator[Path]:
    """Dépôt jetable, installé comme `ROOT` du garde-fou pour la durée du test."""
    with tempfile.TemporaryDirectory() as dossier:
        racine = Path(dossier)
        with mock.patch.object(garde, "ROOT", racine):
            yield racine


class ProjetPythonTest(unittest.TestCase):
    """`projet_python` — quel `pyproject.toml` gouverne un fichier donné."""

    def test_resout_le_pyproject_le_plus_proche(self) -> None:
        """Un fichier du SDK relève du SDK, jamais d'un projet englobant.

        C'est ce qui fait que la largeur de ligne du SDK lui est appliquée, et
        non celle du projet parent qui l'aurait déclaré conforme à tort.
        """
        with depot_temporaire() as racine:
            sdk = racine / "GSIE" / "SDK" / "python"
            (sdk / "src" / "gsie_sdk").mkdir(parents=True)
            (racine / "pyproject.toml").write_text("", encoding="utf-8")
            (sdk / "pyproject.toml").write_text("", encoding="utf-8")
            fichier = sdk / "src" / "gsie_sdk" / "client.py"
            fichier.write_text("", encoding="utf-8")

            self.assertEqual(garde.projet_python(fichier), sdk)

    def test_fichier_sans_pyproject_ancetre_est_hors_perimetre(self) -> None:
        """L'outillage de `tools/` n'a aucune configuration : il reste ignoré.

        Le retour `None` est ce qui l'écarte du contrôle. Le confondre avec la
        racine du dépôt imposerait le défaut de `ruff` à du code aligné à la
        main, sans qu'aucun `pyproject.toml` ne l'ait demandé.
        """
        with depot_temporaire() as racine:
            (racine / "tools").mkdir()
            fichier = racine / "tools" / "check_quelque_chose.py"
            fichier.write_text("", encoding="utf-8")

            self.assertIsNone(garde.projet_python(fichier))

    def test_ne_remonte_jamais_au_dessus_du_depot(self) -> None:
        """Un `pyproject.toml` hors du dépôt ne gouverne rien de ce dépôt.

        Sans cette borne, un `pyproject.toml` traînant dans un dossier parent
        de la machine de développement changerait le verdict de la porte d'un
        poste à l'autre.
        """
        with tempfile.TemporaryDirectory() as dossier:
            parent = Path(dossier)
            (parent / "pyproject.toml").write_text("", encoding="utf-8")
            racine = parent / "depot"
            (racine / "tools").mkdir(parents=True)
            fichier = racine / "tools" / "outil.py"
            fichier.write_text("", encoding="utf-8")

            with mock.patch.object(garde, "ROOT", racine):
                self.assertIsNone(garde.projet_python(fichier))


if __name__ == "__main__":
    unittest.main()
