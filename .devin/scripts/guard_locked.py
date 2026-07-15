"""
Hook PreToolUse — guard-locked
Bloque toute tentative de modification d'un document avec statut Locked.
Reçoit l'événement JSON sur stdin, retourne une décision sur stdout.

Sécurité :
- Path traversal : le chemin cible doit être dans DEVIN_PROJECT_DIR
- Fail-open sur erreur de parsing (comportement sûr pour les non-MD)
- Log stderr pour toute condition anormale (audit)
"""
import json
import os
import sys
from pathlib import Path

LOCKED_MARKER = "Locked"
MAX_LINES_TO_SCAN = 30


def get_project_root() -> Path:
    """Retourne le répertoire racine du projet depuis DEVIN_PROJECT_DIR."""
    root = os.environ.get("DEVIN_PROJECT_DIR", ".")
    return Path(root).resolve()


def is_path_within_project(file_path: str, project_root: Path) -> bool:
    """Vérifie que le chemin cible est bien dans le répertoire projet (anti path traversal)."""
    try:
        target = Path(file_path).resolve()
        target.relative_to(project_root)  # lève ValueError si hors projet
        return True
    except (ValueError, OSError):
        return False


def is_document_locked(file_path: str) -> bool:
    """Lit les premières lignes du fichier et détecte le statut Locked."""
    try:
        path = Path(file_path).resolve()
        if not path.exists() or path.suffix not in {".md", ".mdx"}:
            return False
        with path.open(encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= MAX_LINES_TO_SCAN:
                    break
                # Détecte : | **Statut** | Locked | ou Statut: Locked
                if LOCKED_MARKER in line and ("Statut" in line or "Status" in line):
                    return True
    except OSError as e:
        print(f"[guard-locked] OSError lors de la lecture : {e}", file=sys.stderr)
    return False


def main() -> None:
    project_root = get_project_root()

    try:
        raw = sys.stdin.buffer.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        # Stdin invalide — log pour audit, laisser passer (fail-open intentionnel)
        print(f"[guard-locked] stdin JSON invalide : {e}", file=sys.stderr)
        sys.exit(0)

    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        sys.exit(0)

    # Récupérer le chemin du fichier cible selon le tool
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or ""
    )

    if not file_path:
        sys.exit(0)

    # Vérification anti-path-traversal : le fichier doit être dans le projet
    if not is_path_within_project(file_path, project_root):
        print(
            f"[guard-locked] Chemin hors projet refusé : {file_path}",
            file=sys.stderr,
        )
        # On bloque par précaution : un chemin hors projet est anormal
        decision = {
            "decision": "block",
            "reason": (
                f"Chemin hors du répertoire projet refusé par guard-locked : '{file_path}'. "
                "Vérifier la commande envoyée à l'agent."
            ),
        }
        print(json.dumps(decision))
        sys.exit(0)

    if is_document_locked(file_path):
        name = Path(file_path).name
        print(f"[guard-locked] Tentative de modification d'un Locked : {name}", file=sys.stderr)
        decision = {
            "decision": "block",
            "reason": (
                f"Document LOCKED — '{name}' ne peut pas être modifié directement. "
                "Crée d'abord une RFC dans 02_RFC/ (voir skill /rfc-gsie)."
            ),
        }
        print(json.dumps(decision))

    sys.exit(0)


if __name__ == "__main__":
    main()
