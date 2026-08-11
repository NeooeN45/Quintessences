# info-002 — Architecture GSIE

- **Type** : info
- **Date** : 2026-08-08
- **Salience** : 0.9
- **Importance** : 0.9

14 moteurs GSIE : Evidence, Knowledge, Correlation, Reasoning,
Diagnostic, Recommendation, Validation, GIS, Climate, Pedology,
Botanical, Forest Dynamics, Learning, Simulation.

API : FastAPI dans `GSIE/API/` avec `.venv/` (Python 3.12, uv).
Tests : `tests/unit/`, `tests/integration/`, `tests/mutation/`.
Validation : ruff check + ruff format + mypy + pytest 100% + mutation.

Source : `CLAUDE.md` §9, `AGENTS.md` API
