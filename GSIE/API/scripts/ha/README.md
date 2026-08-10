# Banc haute disponibilité GSIE

Le banc démarre deux replicas API Linux derrière HAProxy. Il utilise le réseau
du Compose principal afin de partager PostgreSQL, Redis et MinIO, sans modifier
la politique FETCH.

```bash
docker compose -f docker-compose.yml up -d db redis minio minio-init mailpit
docker compose -f docker-compose.ha.yml up -d
```

La bordure locale écoute sur `http://127.0.0.1:8088`. Le header
`X-GSIE-Backend` indique le replica choisi uniquement pour les preuves locales.

Retrait sûr d'un replica :

```bash
./scripts/ha/drain_replica.sh api-ha-a
```

La commande crée la sentinelle, exige `/ready=503`, puis accorde 45 secondes à
Gunicorn. Avant toute action sur le second replica, vérifier explicitement que
le premier est revenu dans `X-GSIE-Backend` ; une simple réponse 200 de la
bordure ne suffit pas.

Ce banc qualifie le runtime Linux des conteneurs. Une mesure sur hôte Linux
natif ou CI reste obligatoire avant publication d'une capacité de production.
