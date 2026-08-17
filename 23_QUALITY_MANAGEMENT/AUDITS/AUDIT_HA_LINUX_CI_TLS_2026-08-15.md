# Preuve HA Linux/TLS — run GitHub 31878560746

## Référence

- Workflow : `GSIE HA Linux TLS`.
- Run : [31878560746](https://github.com/NeooeN45/Quintessences/actions/runs/31878560746).
- Branche : `main`.
- Commit testé : `22a1818471055d9f136a98c666b09bf58232780c`.
- Runner : Ubuntu GitHub Actions.
- Durée : 6 min 25 s.
- Conclusion : **success**.

## Séquence validée

Le workflow a exécuté sans échec :

1. construction et initialisation PostgreSQL/Redis/MinIO jetables ;
2. migration et authentification du compte API ;
3. génération d'un certificat TLS éphémère ;
4. démarrage de deux réplicas derrière HAProxy TLS ;
5. charge HTTPS pendant le drainage de `api-ha-a` ;
6. vérification du replica restant ;
7. collecte des journaux et nettoyage complet.

## Résultat de charge

Artefact `ha-linux-drain.json` :

| Mesure | Résultat | Seuil workflow |
|---|---:|---:|
| Requêtes | 6 000 | 6 000 |
| Concurrence | 20 | 20 |
| HTTP 200 | 6 000/6 000 | 100 % |
| Erreurs | 0 | 0 |
| Débit | 271,32 req/s | ≥ 120 req/s |
| p50 | 55,63 ms | — |
| p95 | 177,68 ms | ≤ 250 ms |
| p99 | 267,17 ms | ≤ 400 ms |
| Maximum | 544,34 ms | informatif |

La répartition observée est `replica_a=378` et `replica_b=5 622`, ce qui
confirme que le retrait de A a été pris en compte pendant la campagne. La
sonde `/ready` du proxy restant a également réussi.

## Verdict

**GO pour la preuve de continuité HA Linux/TLS.** Les seuils bloquants sont
respectés, le trafic chiffré reste disponible pendant le drainage et aucun
échec n'est observé.

Cette preuve autorise la qualification technique de la capacité mesurée sur
ce scénario. Elle ne constitue pas encore un SLO produit général : il reste à
tester une route métier longue/idempotente, plusieurs profils de charge et les
dépendances indisponibles avant publication contractuelle.

## Artefacts

- `GSIE/API/tests/perf/results/ha-linux-run-31878560746/ha-linux-drain.json`
- `GSIE/API/tests/perf/results/ha-linux-run-31878560746/ha-linux-containers.log`
- `GSIE/API/tests/perf/results/ha-linux-run-31878560746/ha-linux-platform.log`

## Scénario de dépendance Redis — validation locale

Une régression a été détectée en ajoutant le scénario d'indisponibilité Redis :
le rate limiter partagé bloquait également `/health` lorsque Redis était arrêté.
Les sondes `/health` et `/ready` ne sont donc plus décorées par le rate limiter
applicatif ; leur éventuelle protection est une responsabilité de la bordure.

Sur l'image reconstruite `gsie-ha-test-api:latest`, dans le banc isolé
`gsie-ha-test`, la séquence réelle a produit :

| Étape | Résultat |
|---|---:|
| Redis arrêté | effectué |
| `/ready` via HAProxy TLS | HTTP 503 |
| `/health` interne de `api-ha-a` | HTTP 200 |
| Redis redémarré | effectué |
| `/ready` rétabli | HTTP 200 |

Les tests fonctionnels ciblés `test_health.py` et `test_limiter_contrat.py`
passent à **22/22** en série, avec Ruff, mypy strict et `git diff --check`
propres. Le run GitHub `31878560746` ne contient pas encore cette correction :
le scénario doit être rejoué dans CI après intégration explicite de la
modification. Aucun SLO général n'est publié à ce stade.

## Premier rejeu CI — échec de câblage corrigé

Le rejeu manuel `31881933486` a confirmé le banc HA et le drainage, mais a
échoué uniquement dans le nouveau scénario Redis. La commande de liveness
tentait d'exécuter `/health` dans `api-ha-a`, alors que cette étape avait
intentionnellement drainé ce replica ; GitHub a donc retourné `service
"api-ha-a" is not running`. Il s'agit d'une erreur du test, pas d'un défaut
de l'application.

Le workflow utilise désormais `api-ha-b`, replica restant, pour vérifier que
la liveness demeure indépendante de Redis. Le scénario sera rejoué sous le
nouveau commit avant toute clôture distante.

## Rejeu CI final — validation

Le run manuel `31882759911`, exécuté sur le commit `0298d3f`, est **vert** en
6 min 23 s. Les étapes de construction, démarrage, charge TLS, drainage et
vérification du replica restant passent. Le scénario Redis passe également :

- Redis arrêté → `/ready` via HAProxy TLS attendu en HTTP 503 ;
- `/health` exécuté sur `api-ha-b`, replica survivant, en HTTP 200 ;
- Redis redémarré → `/ready` rétabli avant la fin du délai borné ;
- collecte des diagnostics et nettoyage complet réussis.

La correction de câblage est donc validée à la fois localement et sur Ubuntu
GitHub Actions. Les routes longues/idempotentes et la publication d'un SLO
général restent volontairement hors de cette preuve.
