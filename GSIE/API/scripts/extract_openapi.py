#!/usr/bin/env python3
"""Extrait la spec OpenAPI de l'app FastAPI et l'écrit dans docs/openapi.json.

La spec est générée à runtime par FastAPI (`/api/v1/openapi.json`). En
production, l'endpoint est désactivé (`openapi_url=None` pour production/
staging) — la spec n'est donc accessible qu'en développement. Ce script
l'extrait en important l'app sans démarrer le serveur, et écrit le JSON
dans `docs/openapi.json` pour traçabilité et versionnement.

Usage :
    uv run scripts/extract_openapi.py
    # ou depuis le venv :
    python scripts/extract_openapi.py

Le fichier généré est stable (FastAPI trie les clés) — le diff git ne
montre que les changements réels d'API. Ajouter ce script au CI pour
détecter toute rupture de contrat d'API non documentée.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Résolution d'import : le script tourne depuis la racine du projet API,
# mais src/ n'est pas dans sys.path par défaut en dehors de uv run.
_api_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_api_root / "src"))

from gsie_api.app import app  # noqa: E402

_OUTPUT_PATH = _api_root / "docs" / "openapi.json"


def extract_openapi() -> int:
    """Génère openapi.json et l'écrit sur disque. Retourne 0 si OK, 1 sinon."""
    spec = app.openapi()
    if not isinstance(spec, dict):
        print("ERREUR : openapi() n'a pas retourné un dict", file=sys.stderr)
        return 1

    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys=True + indent=2 → diff git stable et lisible.
    # newline="\n" force LF — la CI tourne sur Linux (LF) et le dépôt
    # normalise en LF via .gitattributes ; sans ça, Windows écrit CRLF
    # et la CI voit un diff sur tous les fichiers.
    _OUTPUT_PATH.write_text(
        json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    n_paths = len(spec.get("paths", {}))
    n_schemas = len(spec.get("components", {}).get("schemas", {}))
    version = spec.get("info", {}).get("version", "?")
    print(
        f"OpenAPI extraite -> {_OUTPUT_PATH.relative_to(_api_root)} "
        f"({n_paths} paths, {n_schemas} schemas, version {version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(extract_openapi())
