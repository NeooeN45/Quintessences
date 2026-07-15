"""
Hook PostToolUse — audit_log
Enregistre chaque modification de fichier dans .devin/audit.log (JSONL).
Ne bloque jamais — exit 0 toujours.

Format : {"timestamp": "...", "tool": "...", "file": "...", "success": bool}
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    try:
        raw = sys.stdin.buffer.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = event.get("tool_name", "unknown")
    tool_input = event.get("tool_input", {})
    tool_response = event.get("tool_response", {})

    file_path = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or ""
    )

    # Ne logger que les modifications de fichiers
    if not file_path:
        sys.exit(0)

    project_root = os.environ.get("DEVIN_PROJECT_DIR", ".")
    log_path = Path(project_root) / ".devin" / "audit.log"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "file": file_path,
        "success": tool_response.get("success", True),
    }

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # Ne jamais bloquer sur un échec de log

    sys.exit(0)


if __name__ == "__main__":
    main()
