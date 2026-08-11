# Épisode 006 — Benchmark performance Correlation Engine

- **Type** : episode
- **Date** : 2026-08-09
- **Loop** : Sécurité+Perf
- **Statut** : réussi
- **Salience** : 0.9
- **Importance** : 0.8

## Résultat

Le calcul Pearson vectorisé `numpy.corrcoef` est 30x à 1521x plus
rapide que la boucle `scipy` pairwise sur les matrices testées.

Point de référence 120 variables :
- 1 000 observations : scipy 2406.70 ms, numpy 1.58 ms, 1521x
- 10 000 observations : scipy 3410.47 ms, numpy 10.45 ms, 326.4x

Le rapport complet est dans `loop_securite_perf.md` et les mesures
brutes dans `GSIE/API/tests/perf/benchmark_output.txt`.
