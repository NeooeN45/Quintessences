# skill-001 — Lancer un benchmark Correlation Engine

- **Type** : skill
- **Date** : 2026-08-08
- **Salience** : 0.9
- **Importance** : 0.7

## Procédure

1. Aller dans `GSIE/API/`
2. Exécuter : `.\.venv\Scripts\python.exe tests\perf\run_benchmark.py`
3. Les résultats s'affichent dans la console
4. Comparer avec la baseline dans `loop_securite_perf.md`

## Backends disponibles

- `scipy` — baseline (lent, 1 paire à la fois)
- `numpy` — vectorisé (326x-1521x plus rapide)
- `nvmath` — GPU (requiert GPU NVIDIA, pas disponible localement)

## Fichiers

- Benchmark : `GSIE/API/tests/perf/benchmark_correlation.py`
- Runner : `GSIE/API/tests/perf/run_benchmark.py`
- Rapport : `GSIE/RESEARCH/BENCHMARK_CORRELATION_ENGINE.md`

Source : `BENCHMARK_CORRELATION_ENGINE.md`
