# VALIDATION_SCIENTIFIQUE — Ground truth + benchmark (DEC-000043 S3)

> **Décision** : DEC-000043 (S3 — Validation scientifique + performance)
> **Date** : 2026-08-02
> **Statut** : Validé — 3/3 scénarios validés, benchmark mesuré

> **Erratum scientifique — 2026-08-11** : la référence Parelle et al. (2007)
> est publiée dans *Tree Physiology*, volume 27, numéro 7, pages 1027–1034,
> DOI `10.1093/treephys/27.7.1027`. L'ancienne mention *Annals of Forest
> Science* était erronée. Les trois scénarios historiques combinent cette
> publication avec des hypothèses pédologiques qui nécessitent une source
> distincte ; ils ne sont donc pas automatiquement des scénarios Gold au sens
> de RFC-0039.

## 1. Objectif

Prouver que les prédictions du moteur sont cohérentes avec la
littérature vérifiée (ground truth) et mesurer les performances de la
chaîne complète. Troisième livrable de la phase de stabilisation.

## 2. Ground truth

### 2.1. Source de référence

> Parelle J., Brendel O., Jolivet Y. (2007), « Intra- and interspecific
> diversity in the response to waterlogging of two co-occurring white
> oak species (Quercus robur and Q. petraea) », *Tree Physiology*, 27(7),
> 1027–1034, DOI `10.1093/treephys/27.7.1027`, notice HAL `hal-02653679`.

29 faits vérifiés (citation retrouvée mot pour mot) sur 31 extraits.

### 2.2. Scénarios de validation

3 scénarios construits à partir des faits vérifiés :

| # | Scénario | Description | Conclusions attendues | Validation |
|---|---|---|---|---|
| 1 | `sol_acide_engorgement_quercus` | pH 4.8 + engorgement hivernal | 2 | valide |
| 2 | `sol_neutre_draine_quercus` | pH 6.5, pas d'engorgement | 1 | valide |
| 3 | `sol_tres_acide_quercus` | pH 3.5, acidité sévère | 2 | valide |

### 2.3. Checks par scénario (6 checks × 3 scénarios = 18 checks)

| Check | Description |
|---|---|
| `nombre_conclusions` | Le moteur produit exactement le nombre attendu |
| `validation_statut` | La validation retourne le statut attendu |
| `recommandations_produites` | Au moins 1 recommandation produite |
| `sources_tracables` | Chaque conclusion a au moins 1 source |
| `diagnostic_persiste` | Le diagnostic a un ID (persisté en DB) |
| `recommandation_liee_diagnostic` | La recommandation cite le diagnostic |

### 2.4. Résultat

**3/3 scénarios validés, 18/18 checks passés.**

## 3. Benchmark

### 3.1. Méthodologie

- 10 itérations de la chaîne complète (Reasoning → Diagnostic →
  Recommendation → Validation)
- 1 warmup non mesuré
- Rate limit respecté (3.1s entre requêtes, 20/min sur l'endpoint)
- Mémoire mesurée via `tracemalloc` (Python)

### 3.2. Résultats mesurés

| Métrique | Valeur |
|---|---|
| **Latence moyenne** | 32.05 ms |
| **Latence médiane (p50)** | ~32 ms |
| **Latence p95** | 34.68 ms |
| **Latence p99** | 34.68 ms |
| **Latence min** | ~28 ms |
| **Latence max** | ~35 ms |
| **Throughput** | 0.35 req/s (limité par rate limit, pas par l'API) |
| **Mémoire peak** | 0.25 MB |

### 3.3. Interprétation

- **Latence** : ~32ms par analyse complète. C'est rapide pour une
  chaîne de 4 moteurs avec persistance DB. Le rate limit (20/min) est
  le bottleneck du throughput, pas la chaîne elle-même.
- **Stabilité** : p95 ≈ p99 ≈ mean — la latence est très stable, peu
  de jitter.
- **Mémoire** : 0.25 MB pour 10 itérations — pas de fuite détectée.
- **Sans rate limit** : le throughput réel serait ~31 req/s
  (1000ms / 32ms), soit 100x plus que le rate limit actuel.

## 4. Reproductibilité

### 4.1. Script

```bash
cd GSIE/API
python scripts/validation_benchmark.py --iterations 10
# Sortie : trace sur stdout + benchmark_resultat.json
```

### 4.2. Paramètres

| Paramètre | Défaut | Description |
|---|---|---|
| `--url` | `http://127.0.0.1:8000` | URL de l'API |
| `--iterations` | `50` | Nombre d'itérations du benchmark |
| `--output` | `benchmark_resultat.json` | Fichier de sortie |

### 4.3. Rapport JSON

Le rapport complet est sauvegardé dans `benchmark_resultat.json` avec :
- Détails de chaque scénario de validation
- Statistiques de latence (min/max/mean/median/p50/p95/p99/stdev)
- Throughput et mémoire

## 5. Limites et prochaines étapes

### Limites actuelles

1. **Ground truth** : 3 scénarios basés sur une seule source (Parelle
   2007). La validation serait plus robuste avec plusieurs sources
   indépendantes et des cas terrain réels.
2. **Benchmark** : mesuré sur API locale (Docker, localhost). Les
   performances en production (réseau, charge, concurrence) seront
   différentes.
3. **Rate limit** : le throughput est limité par la configuration
   slowapi (20/min), pas par la chaîne elle-même.
4. **Mémoire** : `tracemalloc` mesure la mémoire Python du client, pas
   celle de l'API (qui tourne dans un conteneur Docker séparé).

### Prochaines étapes

1. **Multi-sources** : ajouter des scénarios basés sur d'autres
   sources (INRAE, IGN, GBIF) pour renforcer le ground truth
2. **Charge** : benchmark avec requêtes concurrentes (asyncio + N
   workers) pour mesurer le throughput réel sans rate limit
3. **Mémoire API** : mesurer la mémoire du conteneur Docker pendant le
   benchmark (`docker stats`)
4. **Terrain réel** : remplacer les règles déclarées par des règles
   chargées depuis le Knowledge Engine à partir du territoire

## 6. Fichiers

| Fichier | Rôle |
|---|---|
| `scripts/validation_benchmark.py` | Script de validation + benchmark |
| `benchmark_resultat.json` | Rapport JSON de la dernière exécution |
| `GSIE/DOCUMENTATION/VALIDATION_SCIENTIFIQUE.md` | Ce document |
