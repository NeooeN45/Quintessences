# Audit HA local isolé — 2026-08-15

## Objet

Cette campagne vérifie la continuité de service d'une API GSIE derrière
HAProxy avec deux réplicas, un retrait gracieux et une recréation contrôlée.
Elle ne publie aucun SLO de production : l'exécution a lieu sous Docker
Desktop Windows, et non sur un hôte Linux natif.

## Cloisonnement

- Projet Compose : `gsie-ha-test`.
- Base PostgreSQL : `gsie_ha_test`, volumes et réseau dédiés.
- Redis, MinIO et Mailpit : instances `gsie-ha-test_*` dédiées.
- Image API : `gsie-ha-test-api:latest`, construite depuis `cb3c7d6`.
- Migration vérifiée avant démarrage : `20260813_0049`.
- Aucun accès à `gsie-test`, staging ou production.

La limitation de débit applicative a été désactivée uniquement dans un
override ignoré et temporaire, afin de séparer la mesure de capacité de la
mesure de sécurité. Le fichier a été supprimé après la campagne ; la
configuration produit reste inchangée.

## Scénarios exécutés

### 1. Nominal

100 requêtes `GET /health`, concurrence 10 :

| Mesure | Résultat |
|---|---:|
| Succès | 100/100 HTTP 200 |
| Répartition | 50 `replica_a` / 50 `replica_b` |
| Débit | 6,46 req/s |
| p50 | 1 049,90 ms |
| p95 | 3 589,20 ms |
| p99 | 4 170,89 ms |

### 2. Drainage de `replica_a` sous charge

La sentinelle `/tmp/gsie-draining` a été créée pendant 200 requêtes à
concurrence 10. Le replica A a alors renvoyé 503 sur `/ready`, tandis que
HAProxy a continué à servir le trafic par B :

| Mesure | Résultat |
|---|---:|
| Succès | 200/200 HTTP 200 |
| Backends utilisés | 200 `replica_b` |
| Erreurs réseau/HTTP | 0 |
| Débit | 9,60 req/s |
| p95 | 1 942,18 ms |
| p99 | 2 836,51 ms |
| `/ready` A | 503 attendu |
| `/ready` B | 200 |
| `/ready` HAProxy | 200 |

### 3. Arrêt gracieux et recréation

Un second lot de 200 requêtes a été lancé ; A a été drainé puis arrêté avec
un délai de grâce de 45 secondes. Le trafic a été entièrement repris par B :

| Mesure | Résultat |
|---|---:|
| Succès | 200/200 HTTP 200 |
| Backend pendant arrêt | 200 `replica_b` |
| Erreurs réseau/HTTP | 0 |
| Débit | 13,91 req/s |
| p95 | 1 394,91 ms |
| p99 | 1 853,60 ms |

A a ensuite été recréé par Compose. Les deux endpoints internes `/ready`
ont retourné 200 et les deux conteneurs sont redevenus `healthy`.

### 4. Retour dans le pool

Après récupération, 200 requêtes à concurrence 10 ont confirmé le retour des
deux réplicas :

| Mesure | Résultat |
|---|---:|
| Succès | 200/200 HTTP 200 |
| Répartition | 100 `replica_a` / 100 `replica_b` |
| Erreurs réseau/HTTP | 0 |
| Débit | 7,84 req/s |
| p95 | 2 772,30 ms |
| p99 | 3 848,20 ms |

### 5. Route métier réelle et persistance

La route `POST /api/v1/orchestration/analyse` a été testée derrière HAProxy
avec la vérification de persistance dirigée explicitement vers
`gsie_ha_test` :

- campagne nominale : 8/8 HTTP 200 et 8/8 `analysis_run` persistés ;
- campagne pendant drainage de A : 20/20 HTTP 200 et 20/20
  `analysis_run` persistés ; p95 946,14 ms ; tout nouveau trafic après le
  drainage est routé vers B ;
- aucune erreur réseau ou HTTP 5xx observée.

La configuration normale a ensuite été rétablie. La porte de sécurité de la
route a été vérifiée séparément : 21 appels séquentiels donnent 20 HTTP 200,
20 écritures persistées et un HTTP 429 explicite (`20 per 1 minute`). Le
résultat `429` est attendu et ne constitue pas une panne HA.

### 6. TLS et drainage chiffré

Un certificat éphémère avec SAN `127.0.0.1`/`api-ha-edge` a été généré pour
le seul banc. La clé et le certificat correspondent, et `curl` a validé la
chaîne via `--cacert` : `/ready` retourne HTTP 200.

- charge TLS nominale : 100/100 HTTP 200, répartition 50/50, débit
  14,28 req/s, p95 3 334,60 ms ;
- charge TLS pendant drainage de A : 100/100 HTTP 200, 100 % du trafic sur B,
  débit 11,24 req/s, p95 3 660,29 ms, p99 6 976,85 ms ;
- A répond 503 sur `/ready` après la sentinelle de drainage.

La preuve reproduit localement le câblage TLS du workflow
`.github/workflows/ha-linux.yml`. Les seuils de production ne sont pas
transposés à Docker Desktop ; le run Ubuntu distant reste requis.

## Verdict

**PASS pour la continuité locale isolée.** Le retrait gracieux, la reprise
par le replica survivant et le retour du replica recréé sont démontrés sans
perte de requête ni réponse 5xx.

**Non-go production.** Les latences et le débit sont fortement dégradés par
Docker Desktop et ne doivent pas être transformés en capacité annoncée. La
preuve Linux native/TLS du workflow CI reste la référence pour la capacité ;
elle doit être rejouée et rattachée à un identifiant de run avant toute
publication de SLO.

## Artefacts locaux

- `GSIE/API/tests/perf/results/ha_nominal_100_c10_nolimit.json`
- `GSIE/API/tests/perf/results/ha_drain_a_200_c10.json`
- `GSIE/API/tests/perf/results/ha_rolling_stop_a_200_c10.json`
- `GSIE/API/tests/perf/results/ha_post_recovery_200_c10.json`
- `GSIE/API/tests/perf/results/ha_orchestration_8_c2.json`
- `GSIE/API/tests/perf/results/ha_orchestration_drain_a_20_c4_nolimit.json`
- `GSIE/API/tests/perf/results/ha_orchestration_rate_limit_21.json`
- `GSIE/API/tests/perf/results/ha_tls_drain_a_100_c20.json`
