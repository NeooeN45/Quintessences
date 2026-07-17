"""Tests du vérificateur de cohérence de gouvernance (tools/check_governance_consistency.py)."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_governance_consistency import find_unsourced_numeric_constants  # noqa: E402


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


def test_full_repo_scan_reports_no_violation():
    """Exécution complète du script contre le dépôt réel — doit rester à 0 (état actuel connu propre)."""
    script = Path(__file__).resolve().parent / "check_governance_consistency.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=script.parent.parent,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
