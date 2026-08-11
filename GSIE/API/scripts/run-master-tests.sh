#!/usr/bin/env bash
# Master test local — exécute toutes les portes qualité avant un commit.
# Usage : ./scripts/run-master-tests.sh [--mutation]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Environnement virtuel introuvable : $VENV_PYTHON" >&2
    exit 1
fi

cd "$ROOT"

run_step() {
    local title="$1"
    local cmd="$2"
    echo ""
    echo "[MASTER TEST] $title"
    eval "$cmd"
}

MUTATION=0
if [[ "${1:-}" == "--mutation" ]]; then
    MUTATION=1
fi

run_step "Ruff check" "$VENV_PYTHON -m ruff check src tests"
run_step "Ruff format check" "$VENV_PYTHON -m ruff format --check src tests"
run_step "Mypy type check" "$VENV_PYTHON -m mypy src/gsie_api"
run_step "Unit tests with 100% coverage" \
    "$VENV_PYTHON -m pytest tests/unit -q -n 0 --cov=src/gsie_api --cov-report=term-missing"

if [[ "$MUTATION" -eq 1 ]]; then
    run_step "Mutation harness" "$VENV_PYTHON tests/mutation/harnais.py"
fi

echo ""
echo "[MASTER TEST] Toutes les portes qualité sont vertes."
