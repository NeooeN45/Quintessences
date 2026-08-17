# Audit de performance — orchestration complète — 15 août 2026

## Verdict

La route réelle `POST /api/v1/orchestration/analyse` est fonctionnelle sous
concurrence après correction d'une course d'écriture dans le
Recommendation Engine. Chaque réponse 200 observée possède une ligne
`analysis_run` correspondante dans PostgreSQL.

La mesure a été réalisée exclusivement sur la stack Docker `gsie-test` :

- `GSIE_DATABASE_ROLE=test` ;
- `GSIE_DATA_NAMESPACE=gsie-test` ;
- base `gsie_test` ;
- limitation de débit désactivée uniquement pour cette sonde locale ;
- aucune base de production ou de benchmark utilisée.

## Commande reproductible

Depuis `GSIE/API`, après démarrage de la stack de test et montage des clés JWT :

```powershell
$env:PYTHONPATH = "src"
$env:GSIE_JWT_PRIVATE_KEY_PATH = "keys/private.pem"
$env:GSIE_DATABASE_ROLE = "test"
$env:GSIE_DATA_NAMESPACE = "gsie-test"
$env:GSIE_DB_NAME = "gsie_test"
$env:GSIE_API_DB_USER = "gsie_api"
$env:GSIE_API_DB_PASSWORD = "<secret de .env.test.example>"
python scripts/benchmark_orchestration.py --requests 20 --concurrency 5
```

Le script refuse toute base qui ne correspond pas exactement à `gsie_test` et
vérifie les identifiants retournés dans `analysis_run`.

## Résultats

| Scénario | Requêtes | Concurrence | Succès | Erreurs | Persistance | Débit | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Charge nominale | 20 | 5 | 20/20 | 0 | 20/20 | 22,35 req/s | 125,81 ms | 312,87 ms | 312,87 ms |
| Charge renforcée | 40 | 10 | 40/40 | 0 | 40/40 | 26,33 req/s | 268,38 ms | 586,89 ms | 618,09 ms |

Les rapports JSON bruts sont conservés dans :

- `GSIE/API/tests/perf/results/orchestration_20260815_fixed.json` ;
- `GSIE/API/tests/perf/results/orchestration_20260815_c10.json`.

## Défaut découvert et correction

La première sonde (20 requêtes, concurrence 5) a produit **16 succès et 4
HTTP 500**. Les logs PostgreSQL ont identifié une `UniqueViolationError` sur
`resource_pkey` : deux requêtes exécutaient simultanément `GET agent` puis
`INSERT agent` pour l'agent déterministe du Recommendation Engine.

La méthode `_agent` utilise maintenant deux insertions PostgreSQL atomiques
`ON CONFLICT DO NOTHING`, pour `resource` puis `agent`. Cette correction
préserve les identifiants déterministes et supprime la course sans désactiver
les contraintes d'intégrité.

## Contrôles après correction

- tests unitaires Recommendation Engine : **24 passants** ;
- test PostgreSQL concurrent dédié : **1 passant** ; fichier orchestration
  complet : **5 passants** ;
- Ruff sur le moteur, le benchmark et les tests : **OK** ;
- Mypy strict sur le benchmark : **aucune erreur** ;
- images API et outbox-worker reconstruites ;
- six services `gsie-test` sains avant la sonde ;
- aucune erreur 500 pendant les deux campagnes finales ;
- persistance `analysis_run` : **100 %** des réponses réussies.

## Limites d'interprétation

Ces chiffres mesurent Docker Desktop local avec cinq puis dix workers Gunicorn
et une charge synthétique stationnelle. Ils ne constituent pas un SLO de
production. Une campagne Linux multi-réplicas, avec bordure HAProxy et routes
réelles représentatives, reste nécessaire avant toute annonce de capacité.
