# Cloisonnement des environnements de données GSIE

## Règle

Les bases de test, benchmark, staging et production sont des environnements
distincts. Ils ne partagent ni base PostgreSQL, ni volume, ni Redis, ni bucket
MinIO, ni projet Compose. Aucun script de test ou de benchmark ne doit utiliser
les secrets de staging ou de production.

Chaque environnement porte un rôle et un namespace :

| Environnement | Rôle | Namespace | Base | Bucket | Projet Compose |
|---|---|---|---|---|---|
| Développement historique | `development` | `gsie` | `gsie` | `gsie-assets` | `gsie` |
| Tests | `test` | `gsie-test` | `gsie_test` | `gsie-assets-test` | `gsie-test` |
| Benchmark | `benchmark` | `gsie-benchmark` | `gsie_benchmark` | `gsie-assets-benchmark` | `gsie-benchmark` |
| Staging | `staging` | `gsie-staging` | `gsie_staging` | `gsie-assets-staging` | `gsie-staging` |
| Production | `production` | `gsie-production` | `gsie_production` | `gsie-assets-production` | `gsie-production` |

## Démarrage contrôlé

Copier le fichier d'exemple correspondant dans un fichier de secrets local,
puis exécuter le vérificateur avant Compose :

```powershell
python scripts/verify_data_environment.py `
  --environment development `
  --database-role test `
  --namespace gsie-test `
  --database-url postgresql+asyncpg://gsie_api:secret@localhost:55433/gsie_test `
  --object-bucket gsie-assets-test `
  --compose-project gsie-test
```

Le résultat attendu est `ISOLATION_OK`. Une violation doit arrêter le
démarrage, le benchmark ou la campagne CI avant toute connexion.

## Migrations et preuves

- Chaque environnement exécute la même tête Alembic, dans sa propre base.
- Une migration est vérifiée séparément en test puis en staging avant la
  production.
- Les rapports de benchmark indiquent toujours le rôle, le namespace, la tête
  Alembic et le checksum du manifeste utilisé.
- Aucun `docker compose down --volumes` ne doit être exécuté sur production.
- Les volumes historiques de développement sont conservés ; aucune migration
  implicite n'est effectuée par cette règle.
