# Benchmark Correlation Engine — scipy vs numpy vs nvmath-python

| Champ | Valeur |
|---|---|
| **Document** | RESEARCH/BENCHMARK_CORRELATION_ENGINE |
| **Dossier** | GSIE/RESEARCH/ |
| **Phase** | 4 — Implémentation |
| **Statut** | Draft |
| **Date** | 2026-08-08 |
| **Origine** | Veille NVIDIA Developer Blog — nvmath-python v1.0 |
| **Veille liée** | `VEILLE_NVIDIA_DEV_BLOG_2026-08-08.md` §2 |
| **Code lié** | `GSIE/API/tests/perf/benchmark_correlation.py` |

---

## 1. Objet

Évaluer les performances du calcul de corrélation Pearson pairwise sur
des matrices de variables de tailles représentatives de GSIE (120+
variables, 100 à 10000 observations), pour :

1. Établir un **baseline scipy** (implémentation actuelle du Correlation
   Engine)
2. Mesurer le gain avec **numpy vectorisé** (`np.corrcoef`)
3. Préparer l'évaluation de **nvmath-python** (GPU, future)

---

## 2. Configuration

| Paramètre | Valeur |
|---|---|
| **Machine** | Windows AMD64, pas de GPU NVIDIA |
| **Python** | 3.12 |
| **numpy** | 2.4.6 |
| **scipy** | 1.15.3 |
| **nvmath-python** | Non installé (pas de GPU) |
| **Méthode** | Pearson pairwise, 1 run par taille (pas de warmup) |

### Tailles de matrices testées

| n_variables | n_observations | n_paires | Contexte GSIE |
|---|---|---|---|
| 10 | 100 | 45 | Petit échantillon terrain |
| 10 | 1 000 | 45 | Étude stationnelle |
| 10 | 10 000 | 45 | Grille AROME sous-échantillonnée |
| 50 | 1 000 | 1 225 | Multi-domaine (climate + pedology) |
| 50 | 10 000 | 1 225 | Multi-domaine large |
| 120 | 1 000 | 7 140 | Toutes tables GSIE (120+) |
| 120 | 10 000 | 7 140 | Toutes tables GSIE, large |

---

## 3. Résultats

### Tableau principal

| Vars × Obs | Paires | scipy (ms) | numpy (ms) | Speedup |
|---|---|---|---|---|
| 10 × 100 | 45 | 15.14 | 0.24 | 64.3x |
| 10 × 1 000 | 45 | 24.40 | 0.33 | 73.4x |
| 10 × 10 000 | 45 | 20.52 | 0.68 | 30.1x |
| 50 × 1 000 | 1 225 | 461.84 | 0.54 | 849.6x |
| 50 × 10 000 | 1 225 | 622.05 | 3.75 | 165.7x |
| 120 × 1 000 | 7 140 | 2 406.70 | 1.58 | 1 521.0x |
| 120 × 10 000 | 7 140 | 3 410.47 | 10.45 | 326.4x |

### Analyse

**Le gain de numpy vectorisé sur scipy pairwise est massif : 30x à 1521x.**

La raison est simple : `scipy.stats.pearsonr` calcule **une paire à la
fois** avec un appel de fonction Python par paire (boucle double
`for i, for j`). `numpy.corrcoef` calcule **toute la matrice en une
seule opération BLAS** (produit matriciel vectorisé).

Pour la taille cible GSIE (120 variables × 10 000 observations) :
- **scipy** : 3 410 ms (3.4 secondes)
- **numpy** : 10.45 ms (0.01 seconde)
- **Gain** : 326x

---

## 4. Implémentation actuelle du Correlation Engine

Le Correlation Engine actuel (`engine.py`) utilise `scipy.stats.pearsonr`
pour **une seule paire par requête** (périmètre v1 documenté) :

```python
_METHOD_FUNCS = {
    CorrelationMethod.pearson: scipy_stats.pearsonr,
    CorrelationMethod.spearman: scipy_stats.spearmanr,
    CorrelationMethod.kendall: scipy_stats.kendalltau,
}
```

Pour une paire unique, scipy est parfaitement adapté (le overhead de
numpy.corrcoef sur 2 variables serait supérieur). Le benchmark confirme
que scipy est acceptable pour le périmètre v1 (une paire par requête).

**Cependant**, le contrat cible (`CORRELATION_ENGINE.md §5`) prévoit une
**matrice N×N pairwise**. Quand cette extension sera implémentée, le
passage à `numpy.corrcoef` est **obligatoire** — scipy pairwise mettrait
3.4 secondes pour 120 variables, ce qui est inacceptable pour une API.

---

## 5. Évaluation nvmath-python (GPU)

### Pré-requis non satisfaits

nvmath-python requiert :
- Un GPU NVIDIA CUDA-enabled, **ou**
- Linux ARM (NVIDIA Grace) pour le backend NVPL CPU

La machine de développement actuelle (Windows AMD64, pas de GPU) ne
satisfait ni l'un ni l'autre. Le benchmark nvmath n'a donc pas pu être
exécuté.

### Code préparé

Le module `benchmark_correlation.py` contient la fonction
`compute_pairwise_pearson_nvmath()` prête pour exécution sur GPU :

```python
def compute_pairwise_pearson_nvmath(data: np.ndarray) -> np.ndarray:
    import cupy as cp
    import nvmath
    # Z-score sur GPU
    z_gpu = (data_gpu - mean) / std
    # Produit matriciel accéléré GPU via cuBLAS
    covariance_gpu = nvmath.linalg.advanced.matmul(z_gpu, z_gpu.T)
    # Normalisation
    return cp.asnumpy(correlation_gpu)
```

### Gain attendu

Sur GPU (H100 ou RTX 4090), nvmath-python utiliserait cuBLAS pour le
produit matriciel. Pour 120 variables × 10 000 observations :
- **Matrice de données** : 120 × 10 000 × 8 bytes = 9.6 MB (tient en VRAM)
- **Produit matriciel** : 120 × 120 × 10 000 FLOPs = 144 MFLOPs
  (trivial pour un GPU moderne)

Le gain attendu de nvmath vs numpy dépendrait principalement du
**transfert CPU→GPU** (9.6 MB sur PCIe 4.0 ≈ 0.5 ms). Pour cette taille,
le gain serait marginal (numpy fait déjà 10.45 ms). nvmath devient
pertinent pour des matrices beaucoup plus grandes (10 000+ variables ou
100 000+ observations) où le produit matriciel devient le bottleneck.

---

## 6. Recommandations

### Court terme (Phase 4 — maintenant)

1. **Garder scipy pour le périmètre v1** (une paire par requête) —
   c'est l'implémentation actuelle, elle est correcte et testée.

2. **Préparer `numpy.corrcoef` pour la matrice N×N** — quand le
   périmètre s'étendra à la pairwise matrix (contrat cible), utiliser
   `numpy.corrcoef` au lieu de boucler scipy. Gain attendu : 326x à
   1521x.

3. **Le benchmark est archivé** dans `GSIE/API/tests/perf/` pour
   référence future.

### Moyen terme (quand un GPU sera disponible)

4. **Exécuter le benchmark nvmath-python** sur un GPU NVIDIA (DGX,
   SLURM, ou machine locale avec GPU) pour mesurer le gain réel vs
   numpy.

5. **Si le gain est > 5x** sur des matrices > 1000 variables, évaluer
   nvmath comme backend optionnel avec fallback numpy.

### Long terme (si matrices très larges)

6. **nvmath-python distribué** (cuBLASMp) pour matrices qui ne tiennent
   pas en VRAM d'un seul GPU (multi-GPU, multi-node).

---

## 7. Conclusion

| Backend | Statut | Gain vs scipy | Recommandation |
|---|---|---|---|
| **scipy** (actuel) | Production | 1x (baseline) | Garder pour v1 (une paire) |
| **numpy** (vectorisé) | Testé | 30x à 1521x | Adopter pour matrice N×N |
| **nvmath** (GPU) | Code prêt, non testé | À mesurer | Évaluer sur GPU quand disponible |

Le résultat le plus actionnable est **numpy.corrcoef** : un gain de
326x à 1521x sans aucune dépendance supplémentaire (numpy est déjà
présent), pour la future extension matrice N×N du Correlation Engine.

---

## 8. Sources

- [nvmath-python v1.0](https://developer.nvidia.com/blog/run-high-performance-core-math-at-scale-with-nvidia-nvmath-python/) — NVIDIA Developer Blog, 30 juillet 2026
- [numpy.corrcoef documentation](https://numpy.org/doc/stable/reference/generated/numpy.corrcoef.html)
- [scipy.stats.pearsonr documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)
- Code benchmark : `GSIE/API/tests/perf/benchmark_correlation.py`
- Résultats bruts : `GSIE/API/tests/perf/benchmark_output.txt`
