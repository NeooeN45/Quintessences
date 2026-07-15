"""
Hook SessionStart — inject_context
Injecte un résumé de l'état courant du projet dans le contexte de l'agent.
Lit PROJECT_MEMORY.md et extrait les informations clés.

Sécurité :
- Résolution canonique du chemin projet (pas de fallback silencieux sur ".")
- Lecture limitée en taille (60 lignes max)
"""
import json
import os
import sys
from pathlib import Path

MAX_LINES = 60
MAX_SUMMARY_LINES = 40
STATE_SECTION_LINES = 15


def get_project_root() -> Path | None:
    """Retourne le répertoire racine résolu, ou None si non défini."""
    root = os.environ.get("DEVIN_PROJECT_DIR")
    if not root:
        print("[inject-context] DEVIN_PROJECT_DIR non défini — injection ignorée.", file=sys.stderr)
        return None
    resolved = Path(root).resolve()
    if not resolved.is_dir():
        print(f"[inject-context] Répertoire projet invalide : {resolved}", file=sys.stderr)
        return None
    return resolved


def extract_project_summary(project_root: Path) -> str:
    """Extrait les lignes clés de PROJECT_MEMORY.md."""
    memory_path = project_root / "PROJECT_MEMORY.md"
    if not memory_path.exists():
        print(f"[inject-context] PROJECT_MEMORY.md introuvable dans {project_root}", file=sys.stderr)
        return ""

    lines: list[str] = []
    try:
        with memory_path.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= MAX_LINES:
                    break
                lines.append(line.rstrip())
    except OSError as e:
        print(f"[inject-context] Erreur lecture PROJECT_MEMORY.md : {e}", file=sys.stderr)
        return ""

    summary_lines: list[str] = []
    in_state_section = False
    state_count = 0

    for line in lines:
        if line.startswith("## État"):
            in_state_section = True
        if in_state_section and state_count >= STATE_SECTION_LINES:
            break
        if line.strip():
            summary_lines.append(line)
            if in_state_section:
                state_count += 1

    return "\n".join(summary_lines[:MAX_SUMMARY_LINES])


def main() -> None:
    project_root = get_project_root()
    if project_root is None:
        sys.exit(0)

    summary = extract_project_summary(project_root)
    if not summary:
        sys.exit(0)

    context = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "=== ÉTAT COURANT DU PROJET QUINTESSENCES ===\n"
                f"{summary}\n"
                "=== FIN ÉTAT COURANT ===\n\n"
                "Consulte PROJECT_MEMORY.md pour le détail complet avant toute action structurante."
            ),
        }
    }
    print(json.dumps(context, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
