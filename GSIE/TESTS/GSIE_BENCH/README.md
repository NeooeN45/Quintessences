# GSIE-Bench v0.1 - scenarios stationnels v0.2

Cette tranche applique RFC-0039 et DEC-000067 sans ingestion de données et
sans intégration IA.

## Sélection des scénarios

Le catalogue contient trois diagnostics stationnels candidats construits à
partir des dossiers BTS fournis par le Fondateur, chacun décliné en dix
variations contrôlées :

```text
3 diagnostics candidats × 10 variations = 30 scénarios
```

Les scénarios portent la version `0.2.0` et restent
`pending_expert_review`. Ils contiennent désormais les sections contexte,
topographie, climat, pédologie, flore/biodiversité, peuplement, régénération,
historique, gestion, calculs et provenance. Les valeurs observées, déduites,
hypothétiques et manquantes sont séparées.

La référence Parelle 2007 est conservée comme micro-suite historique / Silver
potentielle. Elle ne constitue plus la fondation unique des trois candidats
Gold. Le runner Closed refuse donc toujours l'exécution tant que la relecture
experte et la qualification des sources ne sont pas complétées.

La qualification détaillée est conservée dans
`REFERENCE_QUALIFICATION.md`.

## Contrat exécuté

Le runner se trouve dans `GSIE/API/src/gsie_api/benchmark/` et expose :

- `ScenarioSpec` et `ReferenceRef` : identité, contexte, référence, droits et
  checksum SHA-256 ;
- `DeterministicRunner` : ordre stable, contrôle de qualification, scoring par
  tâche, veto, vérification de checksum, vue candidat aveugle et manifeste de
  run reproductible ;
- `NaiveBaseline` : abstention systématique ;
- `RuleBaseline` : règles stationnelles déterministes explicables, couvrant les
  trois profils v0.2 sans utiliser les réponses attendues.

Les baselines ne consultent aucune réponse privée. Le runner ne transmet jamais
au candidat les labels attendus, les facteurs obligatoires, les veto ou le
statut de qualification. Un résultat `GO` ne vaut
que pour une suite qualifiée et n'entraîne aucune promotion.

## Vérifications

```bash
cd GSIE/API
uv run --extra dev pytest -o addopts='-v --tb=short -n auto --dist=loadfile' \
  tests/unit/test_gsie_bench_runner.py \
  tests/unit/test_gsie_bench_qualification.py \
  tests/unit/test_gsie_bench_conflicts.py -q
```

La revue détaillée se trouve dans `SCENARIO_EXPANSION_REVIEW_2026-08-12.md`.
Le durcissement du runner est consigné dans
`RUNNER_HARDENING_2026-08-15.md`.
La suite exécutable Open/Silver, les métriques et la CLI sont décrites dans
`OPEN_SILVER_IMPLEMENTATION_2026-08-15.md`.
La prochaine action est la relecture experte indépendante des trois diagnostics
et la qualification de leurs droits. Aucun téléchargement ou FETCH n'est
nécessaire pour cette étape.
