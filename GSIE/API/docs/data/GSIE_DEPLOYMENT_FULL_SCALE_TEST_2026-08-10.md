# Redéploiement et test grandeur nature — 2026-08-10

## Verdict

Le redéploiement local du commit `6986e80` est réussi. La chaîne déployée est
fonctionnelle et conserve tous les verrous de gouvernance. Le test ne réalise
aucun nouvel appel SoilGrids : il vérifie le DataAsset réel certifié par
DEC-000061 depuis l'image active reconstruite.

## Preuves déployées

- conteneurs `api-api-1` et `api-outbox-worker-1` sains ;
- cinq workers Gunicorn démarrés ; aucun restart et aucun OOM ;
- `/health` et `/ready` répondent 200 ;
- Alembic `20260810_0048` ;
- registre canonique SoilGrids fermé ;
- `wv003 → wv0033` présent dans l'image active ;
- quatre manifests inchangés au premier passage et au rejeu ;
- objet MinIO temporaire relu, vérifié par SHA-256 puis supprimé ;
- DataAsset SoilGrids relu depuis MinIO : 569 octets, SHA-256
  `a6fd8b120b11e64612cdf3ee22854d8db28413cbe7bd480291cfb203ee24840e`,
  signature TIFF `49492a00` ;
- ligne PostgreSQL cohérente et version `discovered`.

## Charge HTTP

Deux paliers ont été mesurés sur Docker Desktop :

| Palier | Succès | Débit | p95 |
|---|---:|---:|---:|
| 1 000 requêtes, concurrence 100 | 100 % | 18,7 req/s | 15 692 ms |
| 500 requêtes, concurrence 20 | 100 % | 18,9 req/s | 2 195 ms |

Les sondes séquentielles après échauffement répondent en général entre 5 et
8 ms. L'API reste saine à 1,436 Gio sur une limite de 2 Gio. Cette différence
doit être profilée côté Docker Desktop, port forwarding, client HTTP et
middleware avant de fixer une capacité de production.

## Gouvernance

- aucun nouveau `GetCoverage` ;
- aucun nouveau DataAsset SoilGrids ;
- aucune promotion ;
- aucun changement du registre FETCH ;
- les résultats de performance restent dans le dossier local non suivi
  `tests/perf/results/`.
