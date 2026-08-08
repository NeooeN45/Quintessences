# Leçon 005 — numpy.corrcoef vs scipy

- **Date** : 2026-08-08
- **Source** : Benchmark Correlation Engine
- **Contexte** : numpy.corrcoef est massivement plus rapide que scipy pairwise

## Règle

Pour les matrices de corrélation N×N (N > 5 variables), utiliser
`numpy.corrcoef` (vectorisé BLAS) au lieu de boucler `scipy.stats.pearsonr`.
Gain mesuré : 326x à 1521x.

Pour une seule paire (périmètre v1), scipy reste correct (overhead
numpy.corrcoef sur 2 variables serait supérieur).

## Benchmark

| Vars × Obs | scipy (ms) | numpy (ms) | Speedup |
|---|---|---|---|
| 120 × 1000 | 2407 | 1.58 | 1521x |
| 120 × 10000 | 3410 | 10.45 | 326x |

Source : `GSIE/RESEARCH/BENCHMARK_CORRELATION_ENGINE.md`
