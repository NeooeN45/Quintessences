"""Meta-test — conformité des 14 moteurs GSIE.

Vérifie que les 14 moteurs documentés dans GSIE/ENGINES/ ont bien une
implémentation Python correspondante dans gsie_api.engines, avec un
engine.py, un schemas.py et un router.py exposant au moins le endpoint
/status. Détecte les moteurs documentés mais non implémentés (ou
inversement).

Référence : PROJECT_MEMORY.md §9, CLAUDE.md §9, GSIE/ENGINES/README.md.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app

# Les 14 moteurs GSIE (CLAUDE.md §9). Ordre de la chaîne principale +
# moteurs domaine + moteurs transverses.
_ENGINES_ATTENDUS: dict[str, str] = {
    # Chaîne principale
    "evidence": "Evidence Engine (filtre amont)",
    "knowledge": "Knowledge Engine",
    "correlation": "Correlation Engine",
    "reasoning": "Reasoning Engine",
    "diagnostic": "Diagnostic Engine",
    "recommendation": "Recommendation Engine",
    "validation": "Validation Engine",
    # Moteurs domaine
    "gis": "GIS Engine",
    "climate": "Climate Engine",
    "pedology": "Pedology Engine",
    "botanical": "Botanical Engine",
    "forest_dynamics": "Forest Dynamics Engine",
    # Moteurs transverses
    "learning": "Learning Engine",
    "simulation": "Simulation Engine",
}

app = create_app()
client = TestClient(app)


def _engines_implémentés() -> set[str]:
    """Liste les moteurs implémentés (dossiers sous gsie_api.engines).

    Accepte `engine.py` (pattern standard) ou `wrapper.py` (pattern
    Evidence Engine : cœur Rust + wrapper PyO3 + fallback Python).
    """
    engines_dir = Path(__import__("gsie_api.engines", fromlist=["__path__"]).__path__[0])
    return {
        d.name
        for d in engines_dir.iterdir()
        if d.is_dir()
        and not d.name.startswith("__")
        and ((d / "engine.py").exists() or (d / "wrapper.py").exists())
    }


def _engines_documentés() -> set[str]:
    """Liste les moteurs documentés (dossiers sous GSIE/ENGINES/)."""
    repo_root = Path(__file__).resolve().parents[3]
    engines_doc_dir = repo_root / "GSIE" / "ENGINES"
    if not engines_doc_dir.exists():
        pytest.skip(f"Dossier {engines_doc_dir} introuvable")
    return {
        d.name.lower().removesuffix("_engine")
        for d in engines_doc_dir.iterdir()
        if d.is_dir() and d.name.endswith("_ENGINE")
    }


# --- Tests de conformité structurelle ---


def should_have_all_14_engines_implemented() -> None:
    """Les 14 moteurs documentés doivent avoir une implémentation Python."""
    implémentés = _engines_implémentés()
    attendus = set(_ENGINES_ATTENDUS)
    manquants = attendus - implémentés
    assert not manquants, (
        f"Moteurs documentés mais non implémentés : {sorted(manquants)}. "
        f"Implémentés : {sorted(implémentés)}"
    )


def should_have_no_undeclared_engine() -> None:
    """Aucun moteur implémenté ne doit être absent de la liste officielle."""
    implémentés = _engines_implémentés()
    attendus = set(_ENGINES_ATTENDUS)
    orphelins = implémentés - attendus
    assert not orphelins, (
        f"Moteurs implémentés mais non documentés : {sorted(orphelins)}. "
        f"Attendus : {sorted(attendus)}"
    )


def should_have_engine_py_and_schemas_py_for_each_engine() -> None:
    """Chaque moteur implémenté doit avoir engine.py (ou wrapper.py) + schemas.py."""
    implémentés = _engines_implémentés()
    for name in implémentés:
        module_path = Path(__import__("gsie_api.engines", fromlist=["__path__"]).__path__[0]) / name
        has_engine = (module_path / "engine.py").exists() or (module_path / "wrapper.py").exists()
        assert has_engine, f"{name}/engine.py (ou wrapper.py) manquant"
        assert (module_path / "schemas.py").exists(), f"{name}/schemas.py manquant"


# --- Tests de conformité API ---


@pytest.mark.parametrize("engine_name", sorted(_ENGINES_ATTENDUS))
def should_return_200_when_engine_status_requested(engine_name: str) -> None:
    """Chaque moteur doit exposer GET /api/v1/{engine}/status (200).

    Accepte les deux conventions de nommage d'URL : underscore
    (`forest_dynamics`) et tiret (`forest-dynamics`). Le meta-test
    essaie l'underscore en premier, puis le tiret.
    """
    implémentés = _engines_implémentés()
    if engine_name not in implémentés:
        pytest.skip(f"Moteur {engine_name} non implémenté")
    # Essai underscore puis tiret (convention variable selon les moteurs)
    for path_variant in (engine_name, engine_name.replace("_", "-")):
        response = client.get(f"/api/v1/{path_variant}/status")
        if response.status_code == 200:
            data = response.json()
            assert data["engine"] == engine_name or data["engine"] == path_variant
            assert data["status"] in ("active", "degraded", "placeholder")
            return
    pytest.fail(
        f"GET /api/v1/{engine_name}/status (et variantes) -> "
        f"{response.status_code}: {response.text}"
    )


# --- Tests de conformité documentation ---


def should_have_all_engines_documented() -> None:
    """Les 14 moteurs implémentés doivent être documentés dans GSIE/ENGINES/."""
    implémentés = _engines_implémentés()
    documentés = _engines_documentés()
    non_documentés = implémentés - documentés
    assert not non_documentés, (
        f"Moteurs implémentés mais non documentés dans GSIE/ENGINES/ : " f"{sorted(non_documentés)}"
    )


def should_have_readme_for_each_documented_engine() -> None:
    """Chaque moteur documenté doit avoir un README.md."""
    repo_root = Path(__file__).resolve().parents[3]
    engines_doc_dir = repo_root / "GSIE" / "ENGINES"
    if not engines_doc_dir.exists():
        pytest.skip(f"Dossier {engines_doc_dir} introuvable")
    for d in engines_doc_dir.iterdir():
        if d.is_dir() and d.name.endswith("_ENGINE"):
            readme = d / "README.md"
            assert readme.exists(), f"{d.name}/README.md manquant"


# --- Tests de cohérence import ---


@pytest.mark.parametrize("engine_name", sorted(_ENGINES_ATTENDUS))
def should_import_engine_module_without_error(engine_name: str) -> None:
    """Le module gsie_api.engines.{name} doit être importable sans erreur."""
    implémentés = _engines_implémentés()
    if engine_name not in implémentés:
        pytest.skip(f"Moteur {engine_name} non implémenté")
    try:
        importlib.import_module(f"gsie_api.engines.{engine_name}")
    except ImportError as exc:
        pytest.fail(f"Import gsie_api.engines.{engine_name} échoué : {exc}")
