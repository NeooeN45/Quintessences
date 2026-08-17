# Suite Open/Silver GSIE-Bench — 2026-08-15

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-BENCH-OPEN-SILVER-2026-08-15 |
| **Statut** | Draft |
| **Version** | 0.1.0 |
| **Date** | 2026-08-15 |
| **Références** | RFC-0039, DEC-000067 |

## 1. Objet

Cette tranche fournit une suite exécutable sans attendre la relecture des
diagnostics Gold. Elle sert au développement du runner, des baselines et des
rapports, sans produire de preuve Gold ni autoriser une promotion.

## 2. Suite Open/Silver

`build_open_silver_catalog()` construit trois scénarios synthétiques internes :

| Scénario | Cas couvert |
|---|---|
| `silver.open.pedology.001` | classification pédologique nominale |
| `silver.open.missing.002` | abstention devant une donnée critique manquante |
| `silver.open.domain.003` | abstention hors domaine territorial |

Les scénarios sont `silver`, `open`, `qualified` et portent le régime
`synthetic_internal`. Ils ne représentent pas des observations forestières
réelles et ne peuvent pas être utilisés comme vérité scientifique ou porte de
promotion.

La politique `RunPolicy.open_silver()` autorise uniquement les niveaux Silver
et Bronze. Elle refuse les scénarios Gold et exige malgré tout un statut de
qualification explicite.

## 3. Métriques

Le module `gsie_api.benchmark.metrics` fournit des fonctions pures pour :

- précision, rappel, F1 et exact-match multilabel ;
- rappel@k et nDCG@k ;
- p50, p95 et p99 de latence par interpolation déterministe ;
- dégradation relative bornée, y compris lorsque la référence vaut zéro.

Le runner utilise maintenant `classification_metrics` pour son scoring de
diagnostic. Les autres métriques sont prêtes à être branchées aux tâches de
recommandation et aux mesures système lorsque les candidats correspondants
seront intégrés.

## 4. CLI et rapport

La commande locale est :

```text
cd GSIE/API
uv run --extra dev python scripts/gsie_bench.py \
  --suite open-silver --candidate rules
```

Options disponibles :

- `--candidate rules` : baseline pédologique déterministe ;
- `--candidate naive` : baseline d'abstention ;
- `--output rapport.json` : écrit un rapport JSON versionné localement.

Le rapport contient le statut, les métriques, les prédictions brutes, les
évaluations et le `BenchmarkRunManifest`. Il ne contient aucune réponse Gold
privée.

## 5. Vérifications

| Contrôle | Résultat |
|---|---|
| Suite Open/Silver | 3 scénarios qualifiés |
| Baseline règles | `GO`, taux de réussite 1,0 |
| Baseline naïve | non-promotable sur le nominal |
| Tests ciblés cumulés | **25 passants** |
| Registre des moteurs | 14 contrats uniques |
| Ruff + formatage | Passants |
| Mypy strict | Passant |

## 6. Limites et suite

Cette suite est un banc de contrat, pas une validation scientifique. Les
quatorze contrats moteurs sont maintenant enregistrés dans
`gsie_api.benchmark.adapters` et un `EngineBenchmarkAdapter` permet d'injecter
un moteur sans créer automatiquement de session DB, de client réseau ou de
boucle événementielle. Les moteurs asynchrones exigent encore un pont de test
explicite ; aucun moteur réel n'est déclaré exécuté par cette tranche.

Les prochains travaux sont le raccordement contrôlé, moteur par moteur, puis
l'ajout de rapports par tâche et de comparaisons de robustesse.
Les scénarios Gold, l'IA, FETCH et les promotions restent indépendants et
bloqués par leurs gardes respectives.
