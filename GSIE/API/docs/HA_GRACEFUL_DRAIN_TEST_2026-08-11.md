# Haute disponibilité et graceful draining — preuve du 11 août 2026

## Périmètre

Le banc comprend deux replicas de l'image GSIE sous Linux, deux workers par
replica et HAProxy 3.2. Les dépendances PostgreSQL, Redis et MinIO sont celles
du Compose local. Toutes les charges passent par le réseau Docker afin de ne
pas mesurer le port forwarding Docker Desktop.

Cette preuve qualifie un runtime Linux conteneurisé, pas encore un hôte Linux
natif ni la bordure Cloudflare de production.

## Architecture

```text
Client de charge Linux
        ↓
HAProxy :8080
   ↙              ↘
api-ha-a          api-ha-b
   ↘              ↙
PostgreSQL + Redis + MinIO
```

HAProxy contrôle `/ready` toutes les 500 ms. La sentinelle
`/tmp/gsie-draining` force immédiatement un 503 de readiness, avant le cache
DB/Redis. La liveness reste à 200.

## Campagnes nominales

| Route | Requêtes | Concurrence | Succès | Débit | p95 | p99 |
|---|---:|---:|---:|---:|---:|---:|
| `/health` | 3 000 | 20 | 3 000 | 254,53 req/s | 185,71 ms | 282,81 ms |
| `/ready` DB + Redis | 1 000 | 20 | 1 000 | 207,87 req/s | 225,29 ms | 351,01 ms |
| `/api/v1/resources?limit=10` authentifiée | 100 | 5 | 100 | 80,04 req/s | 241,07 ms | 373,57 ms |

Les trois campagnes sont réparties exactement à parts égales entre les deux
replicas. La route `/api/v1/auth/providers` a retourné 60 succès puis 940
réponses 429 sur 1 000 requêtes : le quota Redis distribué est appliqué comme
prévu, cette campagne n'est donc pas une mesure de capacité de la route.

## Drainage d'un replica

Séquence :

```text
charge continue
→ sentinelle sur A
→ /ready A = 503
→ bordure = 200 via B
→ attente de 3 s
→ SIGTERM A, grâce 45 s
```

Résultat sur 6 000 requêtes à concurrence 20 :

- 6 000 réponses 200 ;
- zéro erreur ;
- 237,35 req/s ;
- p95 203,61 ms ;
- p99 314,08 ms ;
- A a servi 1 479 requêtes avant retrait, B 4 521.

## Remplacement et DNS dynamique

Le conteneur A arrêté a été supprimé puis recréé avec une nouvelle adresse.
Le resolver Docker de HAProxy l'a remis en rotation sans redémarrage de la
bordure. L'état final est healthy, sans restart ni OOM.

## Rechargements Gunicorn

Deux rechargements HUP ont été exécutés successivement, avec quinze secondes
d'attente et observation explicite du retour du premier backend avant le
second.

Résultat sur 8 000 requêtes à concurrence 20 :

- 8 000 réponses 200 ;
- zéro erreur ;
- 133,92 req/s ;
- p95 204,22 ms ;
- p99 337,39 ms ;
- maximum 14 125,02 ms ;
- répartition A/B : 4 029 / 3 971.

Le maximum ponctuel reste trop élevé pour annoncer un SLO de production, même
si p95, p99 et disponibilité respectent les critères du laboratoire.

## Contre-preuves indispensables

### Replica unique avec recyclages forcés

Après drainage de A, maintenir longtemps la charge sur B seul avec des seuils
artificiels 1000/1000 a produit 1 307 réponses 503 et une réponse 502 sur
20 000. Les deux workers de B étaient simultanément indisponibles par moments.

### Rechargements trop rapprochés

Attendre seulement cinq secondes et vérifier uniquement que la bordure répond
a conduit à recharger B alors qu'A n'était pas revenu. Résultat : 237 réponses
503 sur 8 000.

Ces échecs valident la règle : deux replicas ne suffisent que si les opérations
sont séquencées sur l'état réel de chaque backend.

## Ressources finales

- replica A : 601,4 MiB ;
- replica B : 601,4 MiB ;
- HAProxy : 13,37 MiB ;
- aucun OOM ;
- aucun restart de conteneur.

## Critères provisoires et suite

Le laboratoire retient zéro erreur, p95 ≤ 250 ms, p99 ≤ 400 ms et au moins
120 req/s pour les routes légères. Avant publication d'une capacité :

1. reproduire sous Linux natif ou CI ;
2. tester TLS et la bordure réelle ;
3. tester écritures idempotentes et requêtes longues ;
4. automatiser l'attente du retour backend dans le déploiement ;
5. réduire et expliquer le maximum observé à 14,1 s ;
6. définir ensuite seulement les SLO de production.
