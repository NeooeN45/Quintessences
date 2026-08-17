# Durcissement du runner GSIE-Bench — 2026-08-15

| Champ | Valeur |
|---|---|
| **Identifiant** | GSIE-BENCH-RUNNER-HARDENING-2026-08-15 |
| **Statut** | Draft |
| **Version** | 0.1.1 |
| **Date** | 2026-08-15 |
| **Références** | RFC-0039, DEC-000067 |

## 1. Objet

Cette tranche durcit le runner déterministe avant la première exécution Closed.
Elle ne qualifie aucun scénario, ne lance aucun FETCH et n'intègre aucun modèle
IA. Elle traite exclusivement l'aveuglement du candidat et l'intégrité des
manifestes.

## 2. Correction critique : vue candidat aveugle

Avant cette tranche, `DeterministicRunner` transmettait directement le
`ScenarioSpec` au candidat. Celui-ci pouvait donc lire par erreur les champs
servant au scoring : labels attendus, facteurs obligatoires, recommandations
interdites et statut de qualification.

Le runner construit maintenant une `CandidateScenario` distincte contenant
uniquement :

- l'identité et la version du contrat ;
- le territoire et la période déclarés ;
- les entrées du scénario.

Les réponses attendues, les vetos, les droits et la qualification restent dans
le runner et ne franchissent pas la frontière candidat. Les baselines ne
dépendent plus du nom de la variation ni de `expected_behavior` ; elles
déduisent l'abstention à partir des signaux présents dans les entrées.

## 3. Intégrité et immutabilité

- Le checksum SHA-256 du scénario est recalculé avant tout appel candidat.
- Une divergence lève `ScenarioIntegrityError` et aucun candidat n'est appelé.
- Les dictionnaires, listes et ensembles des entrées sont figés récursivement.
- La sérialisation du checksum est canonique et stable pour les structures
  imbriquées.

## 4. Vérifications reproduites

Chaque run retourne maintenant un `BenchmarkRunManifest` immuable avec
l'identité du candidat, la version de suite, les identifiants et checksums des
scénarios, les prédictions brutes et leurs checksums, les checksums des
évaluations et l'empreinte du résultat public.
Deux exécutions identiques produisent le même `run_id` et le même checksum de
manifeste.

| Contrôle | Résultat |
|---|---|
| Tests GSIE-Bench ciblés | **14 passants** |
| Test de non-fuite des réponses privées | Passant |
| Test de checksum altéré avant appel | Passant |
| Test d'entrée candidate immuable | Passant |
| Manifeste reproductible et immuable | Passant |
| Ruff package + tests | Passant |
| Mypy strict package | Passant |

La commande de test ciblée est :

```text
uv run --extra dev pytest -o addopts='-v --tb=short -n auto --dist=loadfile' \
  tests/unit/test_gsie_bench_runner.py \
  tests/unit/test_gsie_bench_qualification.py \
  tests/unit/test_gsie_bench_conflicts.py -q
```

La porte de couverture globale du projet n'est pas interprétable sur cette
tranche isolée : elle mesure l'ensemble de `gsie_api`, pas seulement le package
GSIE-Bench. Elle n'est donc pas utilisée comme preuve de couverture de ce
durcissement ; les tests ciblés, Ruff et mypy sont les preuves pertinentes.

## 5. Limites conservées

- Les trente scénarios restent `pending_expert_review`.
- Une exécution Closed complète reste refusée par `QualificationRequiredError`.
- Les seuils scientifiques, les réponses alternatives et les droits
  d'annotation doivent encore être validés par la relecture experte.
- Le runner n'effectue aucun accès réseau, aucune ingestion et aucune
  promotion.

## 6. Prochaine étape autorisée

Poursuivre la relecture indépendante des trois diagnostics, enregistrer les
avis et la qualification juridique, puis figer un manifeste Closed séparé.
Une première mesure ne pourra être exécutée qu'après cette qualification.
