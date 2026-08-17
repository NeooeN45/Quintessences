"""Tests du vérificateur de cohérence de gouvernance (tools/check_governance_consistency.py)."""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_governance_consistency import (  # noqa: E402
    find_unsourced_numeric_constants,
    verifier_chemins_livrables,
    verifier_coherence_statuts,
    verifier_directives_actives,
    verifier_fences_markdown,
    verifier_memoires_courantes,
    verifier_phases_cloturees,
)


def test_sourced_threshold_constant_is_not_flagged():
    """Un seuil décimal avec une citation dans les lignes précédentes ne doit pas être signalé."""
    text = """
# Seuils de force de corrélation — Evans (1996), échelle usuelle en
# biostatistique pour |r|.
_STRENGTH_THRESHOLDS: list[tuple[float, str]] = [
    (0.80, "very_strong"),
    (0.60, "strong"),
]
"""
    assert find_unsourced_numeric_constants(text) == []


def test_unsourced_threshold_constant_is_flagged():
    """Un seuil décimal sans aucune citation à proximité doit être signalé."""
    text = """
_INVENTED_THRESHOLD = 0.73
"""
    assert find_unsourced_numeric_constants(text) == ["_INVENTED_THRESHOLD"]


def test_governance_reference_counts_as_citation():
    """Une référence RFC-/ADR-/DEC-/CON- à proximité vaut citation."""
    text = """
# Seuil défini par RFC-0014 §3.4
_SEUIL_CONFIANCE = 0.5
"""
    assert find_unsourced_numeric_constants(text) == []


def test_integer_only_constant_is_not_flagged():
    """Une constante entière (rang ordinal, retries, etc.) n'est pas un seuil scientifique."""
    text = """
_MAX_RETRIES = 4
_EVIDENCE_RANKS: dict[str, int] = {"A": 6, "B": 5}
"""
    assert find_unsourced_numeric_constants(text) == []


def test_multiline_dict_constant_is_scanned_as_one_block():
    """Un dict multi-lignes doit être traité comme un seul bloc (parenthèses/accolades équilibrées)."""
    text = """
_MAPPING = {
    "a": 1,
    "b": 2.5,
}
"""
    assert find_unsourced_numeric_constants(text) == ["_MAPPING"]


def test_source_reference_constructor_is_not_flagged():
    """Un littéral décimal dans un URL de version (v2.0) au sein d'une SourceReference(...)
    ne doit pas être signalé — la SourceReference EST déjà la citation structurée."""
    text = """
_SOILGRIDS_SOURCE = SourceReference(
    type_source=SourceType.peer_reviewed,
    auteur="Poggio, L. et al.",
    date_publication="2021",
    reference="rest.isric.org/soilgrids/v2.0/properties/query",
)
"""
    assert find_unsourced_numeric_constants(text) == []


def test_citation_with_et_al_is_recognized():
    """Le format « Nom et al. (Année) » doit être reconnu comme citation."""
    text = """
# Rameau et al. (2008) — seuils d'autécologie
_PH_SEUIL = 4.5
"""
    assert find_unsourced_numeric_constants(text) == []


def test_statuts_tete_et_pied_contradictoires_sont_signales():
    texte = """# Exemple

| **Statut** | Validated |

Contenu.

> Statut : *Draft — à relire.*
"""

    assert verifier_coherence_statuts(texte) == [
        "statuts contradictoires : draft, validated"
    ]


def test_mentions_de_statut_dans_le_corps_ne_sont_pas_des_metadonnees():
    texte = """# Exemple

| **Statut** | Validated |

| Choix | Statut |
|---|---|
| Import | Draft |
"""

    assert verifier_coherence_statuts(texte) == []


def test_fence_markdown_non_fermee_est_signalee_comme_troncature():
    texte = """# Schéma

```sql
CREATE TABLE utilisateurs (
    nom_utilisateur
"""

    assert verifier_fences_markdown(texte) == [
        "fence Markdown ``` non fermée (troncature probable)"
    ]


def test_fences_markdown_equilibrees_ne_sont_pas_signalees():
    assert verifier_fences_markdown("```sql\nSELECT 1;\n```\n") == []


def test_restauration_livrable_309_preserve_le_fragment_historique():
    """Le scellement 309 doit rester append-only et rendre le Markdown lisible."""
    racine = Path(__file__).resolve().parents[1]
    chemin = racine / "GSIE" / "ARCHITECTURE" / "ENCYCLOPEDIA_DATABASE_SCHEMA.md"
    contenu = chemin.read_bytes()
    marqueur = b"-- [TRONCATURE HISTORIQUE CONSTATEE]"

    fragment, scellement = contenu.split(marqueur, maxsplit=1)
    entete_git = f"blob {len(fragment)}\0".encode()
    empreinte = hashlib.sha1(entete_git + fragment).hexdigest()

    assert empreinte == "f1a68789752fe7751b20aa99fbdec0df587d6f96"
    assert b"Aucun SQL manquant n'a ete reconstitue." in scellement
    assert verifier_fences_markdown(contenu.decode("utf-8")) == []


def test_phase_cloturee_avec_livrable_draft_est_signalee():
    texte = """## Phase 2 — Architecture (clôturée ✅)

| # | Livrable | Fichier / Dossier | Statut |
|---|---|---|---|
| 201 | Architecture | `architecture.md` | Draft |
| 202 | Contrats | `contrats.md` | Validated |

## Phase 3 — Connaissance (active)
| 301 | Méthode | `methode.md` | Draft |
"""

    assert verifier_phases_cloturees(texte) == [
        "Phase 2 clôturée avec le livrable 201 au statut Draft"
    ]


def test_chemin_inexistant_de_livrable_est_signale(tmp_path):
    (tmp_path / "present.md").write_text("ok", encoding="utf-8")
    texte = """| # | Livrable | Fichier / Dossier | Statut |
|---|---|---|---|
| 001 | Présent | `present.md` | Validated |
| 002 | Absent | `absent.md` | Validated |
"""

    assert verifier_chemins_livrables(texte, tmp_path) == [
        "livrable 002 : chemin inexistant `absent.md`"
    ]


def test_chemin_glob_de_livrable_est_accepte_si_une_cible_existe(tmp_path):
    moteur = tmp_path / "GSIE" / "ENGINES" / "EVIDENCE_ENGINE"
    moteur.mkdir(parents=True)

    texte = "| 207 | Moteurs | `GSIE/ENGINES/*/` (14 dossiers) | Draft |"

    assert verifier_chemins_livrables(texte, tmp_path) == []


def test_directive_non_active_dans_active_est_signalee(tmp_path):
    dossier = tmp_path / "01_DIRECTIVES" / "ACTIVE"
    dossier.mkdir(parents=True)
    (dossier / "GSIE-DIR-0001.md").write_text(
        "# Directive\n# Statut : ACTIVE\n", encoding="utf-8"
    )
    (dossier / "GSIE-DIR-0002.md").write_text(
        "# Directive\n# Statut : Draft\n", encoding="utf-8"
    )

    assert verifier_directives_actives(tmp_path) == [
        "01_DIRECTIVES/ACTIVE/GSIE-DIR-0002.md : statut `draft` dans ACTIVE/"
    ]


def test_directives_draft_et_review_sont_acceptees_dans_proposed(tmp_path):
    dossier = tmp_path / "01_DIRECTIVES" / "PROPOSED"
    dossier.mkdir(parents=True)
    (dossier / "GSIE-DIR-0001.md").write_text(
        "# Directive\n# Statut : Draft\n", encoding="utf-8"
    )
    (dossier / "GSIE-DIR-0002.md").write_text(
        "# Directive\n# Statut : Review\n", encoding="utf-8"
    )

    assert verifier_directives_actives(tmp_path) == []


def test_directive_active_dans_proposed_est_signalee(tmp_path):
    dossier = tmp_path / "01_DIRECTIVES" / "PROPOSED"
    dossier.mkdir(parents=True)
    (dossier / "GSIE-DIR-0001.md").write_text(
        "# Directive\n# Statut : ACTIVE\n", encoding="utf-8"
    )

    assert verifier_directives_actives(tmp_path) == [
        "01_DIRECTIVES/PROPOSED/GSIE-DIR-0001.md : statut `active` "
        "incompatible avec PROPOSED/ (attendus : draft, review)"
    ]


def test_directive_close_est_acceptee_dans_archived(tmp_path):
    dossier = tmp_path / "01_DIRECTIVES" / "ARCHIVED"
    dossier.mkdir(parents=True)
    (dossier / "GSIE-DIR-0007.md").write_text(
        "# Directive\n# Statut : CLOS\n", encoding="utf-8"
    )

    assert verifier_directives_actives(tmp_path) == []


def test_plusieurs_directives_de_phase_actives_sont_signalees(tmp_path):
    dossier = tmp_path / "01_DIRECTIVES" / "ACTIVE"
    dossier.mkdir(parents=True)
    for numero in ("0003", "0011"):
        (dossier / f"GSIE-DIR-{numero}.md").write_text(
            "# Directive\n# Statut : ACTIVE\n# Classification : PHASE\n",
            encoding="utf-8",
        )

    assert verifier_directives_actives(tmp_path) == [
        "plusieurs directives de phase actives : GSIE-DIR-0003.md, "
        "GSIE-DIR-0011.md"
    ]


def test_memoires_courantes_contradictoires_sont_signalees(tmp_path):
    archive = tmp_path / "22_PROJECT_MEMORY"
    archive.mkdir()
    (tmp_path / "PROJECT_MEMORY.md").write_text(
        "| **Phase** | 4 — Implémentation |\n"
        "| **Directive courante** | GSIE-DIR-0011 |\n",
        encoding="utf-8",
    )
    (archive / "PROJECT_MEMORY.md").write_text(
        "| **Phase** | 4 — Implémentation |\n"
        "| **Directive courante** | GSIE-DIR-0003 |\n",
        encoding="utf-8",
    )

    assert verifier_memoires_courantes(tmp_path) == [
        "mémoires courantes contradictoires pour `Directive courante` : "
        "GSIE-DIR-0003, GSIE-DIR-0011"
    ]


def test_memoires_courantes_alignees_ne_sont_pas_signalees(tmp_path):
    archive = tmp_path / "22_PROJECT_MEMORY"
    archive.mkdir()
    contenu = (
        "| **Phase** | 4 — Implémentation |\n"
        "| **Directive courante** | GSIE-DIR-0011 |\n"
    )
    (tmp_path / "PROJECT_MEMORY.md").write_text(contenu, encoding="utf-8")
    (archive / "PROJECT_MEMORY.md").write_text(contenu, encoding="utf-8")

    assert verifier_memoires_courantes(tmp_path) == []


def test_memoire_explicitement_archivee_n_est_pas_comparee(tmp_path):
    archive = tmp_path / "22_PROJECT_MEMORY"
    archive.mkdir()
    (tmp_path / "PROJECT_MEMORY.md").write_text(
        "| **Phase** | 4 — Implémentation |\n"
        "| **Directive courante** | GSIE-DIR-0011 |\n",
        encoding="utf-8",
    )
    (archive / "PROJECT_MEMORY.md").write_text(
        "| **État documentaire** | Archive |\n"
        "| **Superseded by** | ../PROJECT_MEMORY.md |\n"
        "| **Phase** | 1 — Foundation |\n"
        "| **Directive courante** | GSIE-DIR-0003 |\n",
        encoding="utf-8",
    )

    assert verifier_memoires_courantes(tmp_path) == []
