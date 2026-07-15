"""
Hook PreToolUse — pre-commit-gsie
Valide les commits GSIE avant qu'ils ne soient créés.
Vérifie : conventional commits, description en français, pas de secrets, pas de .env.

Déclencheur : PreToolUse sur exec quand la commande commence par 'git commit'.
"""
import json
import re
import sys
from pathlib import Path

# Patterns de commits valides (Conventional Commits)
VALID_COMMIT_RE = re.compile(
    r"^(feat|fix|refactor|test|docs|chore|perf|ci|revert|build|style)"
    r"(\([\w\-]+\))?"
    r":\s+.+",
    re.IGNORECASE
)

# Mots qui indiquent un commit en anglais (à éviter pour GSIE)
ENGLISH_INDICATORS = {
    "add", "fix", "update", "remove", "delete", "implement", "create",
    "change", "modify", "improve", "refactor", "optimize", "clean",
    "rename", "move", "replace", "introduce", "support", "handle",
    "resolve", "prevent", "ensure", "allow", "enable", "disable"
}

# Patterns de secrets à bloquer
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36}", re.IGNORECASE),  # GitHub tokens
    re.compile(r"cog_[A-Za-z0-9]{40}", re.IGNORECASE),        # Devin API keys
    re.compile(r"AKIA[A-Z0-9]{16}"),                           # AWS access keys
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9]{48}"),                         # OpenAI keys
    re.compile(r"password\s*=\s*['\"](?!test|gsie_test|changeme|password|secret|example|fake|dummy)[^'\"]{12,}['\"]", re.IGNORECASE),
]

# Fichiers de test où les faux secrets sont acceptables
TEST_FILE_PATTERNS = {"test_", "_test", "conftest", "fixtures", "mock"}

# Fichiers qui ne doivent jamais être committés
FORBIDDEN_FILES = [
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.staging", ".env.test",
]


def extract_commit_message(tool_input: dict) -> str | None:
    """Extrait le message de commit depuis la commande git."""
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.startswith("git commit"):
        return None

    # Chercher -m "message" ou -m 'message'
    match = re.search(r"-m\s+['\"](.+?)['\"]", command)
    if match:
        return match.group(1)

    # Chercher -m message (sans quotes)
    match = re.search(r"-m\s+(\S+)", command)
    if match:
        return match.group(1)

    return None


def check_english_message(message: str) -> bool:
    """Vérifie si le message de commit semble en anglais."""
    # Extraire la description (après le type:)
    parts = message.split(":", 1)
    if len(parts) < 2:
        return False

    description = parts[1].strip().lower()
    words = re.findall(r"\b\w+\b", description)

    # Si >50% des mots sont des indicateurs anglais → probablement anglais
    english_count = sum(1 for w in words if w in ENGLISH_INDICATORS)
    return len(words) > 0 and english_count / len(words) > 0.5


def check_secrets_in_staged_files() -> str | None:
    """Vérifie qu'aucun secret n'est dans les fichiers staged."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None

        files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        for filepath in files:
            if not filepath:
                continue

            # Vérifier les noms de fichiers interdits
            basename = Path(filepath).name
            if basename in FORBIDDEN_FILES:
                return f"Fichier interdit dans le commit : {filepath} (contient des secrets potentiels)"

            # Vérifier le contenu des fichiers staged
            if Path(filepath).suffix in {".py", ".ts", ".js", ".kt", ".json", ".yaml", ".yml", ".env"}:
                # Ignorer les fichiers de test pour les patterns password (faux positifs)
                is_test_file = any(p in filepath.lower() for p in TEST_FILE_PATTERNS)
                diff_result = subprocess.run(
                    ["git", "diff", "--cached", filepath],
                    capture_output=True, text=True, timeout=5
                )
                if diff_result.returncode == 0:
                    diff_content = diff_result.stdout
                    for pattern in SECRET_PATTERNS:
                        # Skip password pattern pour les fichiers de test (faux positifs)
                        if is_test_file and "password" in pattern.pattern:
                            continue
                        if pattern.search(diff_content):
                            return f"Secret détecté dans {filepath} : pattern {pattern.pattern[:30]}..."

    except Exception:
        pass  # Ne jamais bloquer sur une erreur de scan

    return None


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        sys.exit(0)

    # Cet hook ne s'applique qu'aux commandes git commit
    command = tool_input.get("command", "")
    if not isinstance(command, str) or "git commit" not in command:
        sys.exit(0)

    # 1. Vérifier les secrets dans les fichiers staged
    secret_error = check_secrets_in_staged_files()
    if secret_error:
        decision = {
            "decision": "block",
            "reason": f"SÉCURITÉ — {secret_error}. Retire le fichier du staging ou supprime le secret."
        }
        print(json.dumps(decision))
        sys.exit(0)

    # 2. Vérifier le format du commit
    message = extract_commit_message(tool_input)
    if message:
        if not VALID_COMMIT_RE.match(message):
            decision = {
                "decision": "block",
                "reason": (
                    f"Commit non conforme à Conventional Commits : '{message[:50]}...'. "
                    "Format requis : type(scope): description. "
                    "Types : feat, fix, refactor, test, docs, chore, perf, ci, revert."
                )
            }
            print(json.dumps(decision))
            sys.exit(0)

        # 3. Vérifier que le message est en français
        if check_english_message(message):
            decision = {
                "decision": "block",
                "reason": (
                    f"Commit en anglais détecté : '{message[:50]}...'. "
                    "GSIE exige les commits en français. "
                    "Exemple : 'feat(api): ajoute rotation des refresh tokens'"
                )
            }
            print(json.dumps(decision))
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
