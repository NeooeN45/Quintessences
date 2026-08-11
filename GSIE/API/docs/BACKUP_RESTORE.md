# Sauvegarde et restauration PostgreSQL — GSIE

| Champ | Valeur |
|---|---|
| **ID** | DOC-BACKUP-001 |
| **Statut** | Implémenté — validé en direct le 2026-08-08 (voir §3.6 et `GSIE/DOCUMENTATION/DR-RESTAURATION.md` §3.5) |
| **Date** | 2026-07-27 (config initiale) — 2026-08-08 (implémentation + validation) |
| **Référence** | DEC-000037, DEC-000019 |
| **Périmètre** | PostgreSQL 16 + PostGIS 3.4 + Apache AGE (151 tables) |

---

## 1. Vue d'ensemble

GSIE utilise deux stratégies de sauvegarde complémentaires :

| Stratégie | Outil | RPO | RTO | Usage |
|---|---|---|---|---|
| **Quick win** | `pg_dump` (script) | 24h | 30 min | Dev, staging, backup manuel |
| **Cible production** | `pgBackRest` | 5 min | 15 min | Production, PITR, DR |

Le runbook DR complet est dans
`23_QUALITY_MANAGEMENT/PROCESSES/DISASTER_RECOVERY_DB.md`.

---

## 2. Quick win — pg_dump

### 2.1 Backup manuel

```bash
./scripts/backup_pgdump.sh ./backups
```

Le script :
- utilise `pg_dump -Fc` (format custom, compressé) ;
- nomme le fichier `gsie_backup_YYYYMMDD_HHMMSS.dump` ;
- effectue une rotation (garde les 7 derniers backups) ;
- lit les credentials depuis les variables d'environnement
  (`GSIE_DB_HOST`, `GSIE_DB_PORT`, `GSIE_DB_USER`, `GSIE_DB_PASSWORD`,
  `GSIE_DB_NAME`).

### 2.2 Restauration depuis pg_dump

```bash
# 1. Arrêter l'API
docker compose stop api outbox-worker

# 2. Restaurer
PGPASSWORD="$GSIE_DB_PASSWORD" \
  pg_restore -h localhost -p 5432 -U gsie -d gsie \
  --no-owner --no-privileges --clean --if-exists \
  ./backups/gsie_backup_YYYYMMDD_HHMMSS.dump

# 3. Vérifier
./scripts/test_restore.sh ./backups/gsie_backup_YYYYMMDD_HHMMSS.dump

# 4. Redémarrer
docker compose start api outbox-worker
```

### 2.3 Test de restauration

```bash
./scripts/test_restore.sh <backup_file.dump>
```

Le script :
- crée une base temporaire `gsie_restore_test_<timestamp>` ;
- restaure le backup avec `pg_restore` ;
- vérifie le nombre de tables (≥ 116) ;
- vérifie PostGIS (`PostGIS_Version()`) ;
- vérifie Apache AGE (requête Cypher `RETURN 1`) ;
- supprime la base temporaire.

---

## 3. Cible production — pgBackRest

### 3.1 Configuration

La configuration template est dans `docker/pgbackrest.conf`.

Points clés :
- **Chiffrement AES-256-CBC** des backups (at-rest) ;
- **Compression zstd** (rapide + bon ratio) ;
- **Block incremental backup** (sauvegarde au niveau du bloc, pas du
  fichier — gain massif sur les tables PostGIS volumineuses) ;
- **Multi-repo** : repo1 local (RTO court) + repo2 S3 cross-région
  (DR long terme) ;
- **Archivage asynchrone** des WAL (évite de ralentir les COMMIT).

### 3.2 postgresql.conf requis

```ini
wal_level = replica
archive_mode = on
archive_command = 'pgbackrest --stanza=gsie archive-push %p'
archive_timeout = 300
max_wal_senders = 6
```

### 3.3 Planification (cron)

pgbackrest et son dépôt vivent uniquement dans le conteneur/volume `db` —
l'hôte ne peut pas invoquer `pgbackrest` directement, il passe par
`scripts/pgbackrest_backup.sh` (wrapper `docker exec`) :

```cron
# Full hebdomadaire (dimanche 01h00)
0 1 * * 0 /path/to/GSIE/API/scripts/pgbackrest_backup.sh full

# Diff quotidien (lundi-samedi 01h00)
0 1 * * 1-6 /path/to/GSIE/API/scripts/pgbackrest_backup.sh diff

# Incrémental toutes les 30 minutes
*/30 * * * * /path/to/GSIE/API/scripts/pgbackrest_backup.sh incr

# Vérification quotidienne (06h00)
0 6 * * * docker exec -u postgres api-db-1 pgbackrest --stanza=gsie check
```

L'archivage WAL continu (RPO ≤ 5 min) est indépendant de ce planning — il
tourne en permanence via `archive_command` sur le serveur PostgreSQL
(§3.2), déclenché par PostgreSQL lui-même à chaque bascule de segment.

### 3.4 PITR (Point-in-Time Recovery)

```bash
# Restaurer à un timestamp précis
pgbackrest --stanza=gsie --type=time \
  --target="2026-07-27 14:30:00+02" \
  --target-action=promote \
  restore

# Restaurer à un restore point nommé
pgbackrest --stanza=gsie --type=name \
  --target="avant_migration_v42" \
  --target-action=promote \
  restore
```

**Bonne pratique** : créer un restore point nommé avant chaque migration
Alembic critique :

```sql
SELECT pg_create_restore_point('avant_migration_202607');
```

### 3.5 Points d'implémentation vérifiés

- **Connexion locale** : `pg1-socket-path`, jamais `pg1-host` (réservé à
  un accès SSH distant — le conteneur `db` exécute pgbackrest lui-même).
- **Passphrase de chiffrement** : jamais écrite dans `pgbackrest.conf`
  (le fichier n'interprète pas `${VAR}`, ce n'est pas un script shell) —
  lue nativement par pgbackrest depuis la variable d'environnement
  `PGBACKREST_REPO1_CIPHER_PASS` du conteneur.
- **Rôle `pg1-user`** : `gsie` (le rôle SUPERUSER réel créé par l'image
  officielle). Le template initial référençait `gsie_migrator`, un rôle
  du schéma à 3 comptes de DEC-000037 jamais câblé dans
  `docker-entrypoint-initdb.d` — remplacé par les rôles réellement
  déployés (`gsie`, `gsie_api`/`api_user`, `gsie_viz`/`viz_user`,
  migration `20260801_0025`).

### 3.6 Validation live (2026-08-08)

Testé en conditions réelles sur la base de développement (52 MB, 151
tables) : `stanza-create` (online), archivage WAL (manuel et automatique
via `archive_command`), sauvegarde complète chiffrée AES-256-CBC, et
restauration dans un répertoire isolé avec promotion automatique — parité
exacte (151 = 151 tables) et PostGIS fonctionnel sur l'instance restaurée.
Détail complet : `GSIE/DOCUMENTATION/DR-RESTAURATION.md` §3.5.

**Reste à faire** : `docker compose build db` pour figer pgbackrest dans
`Dockerfile.db` de façon permanente (la validation a reconfiguré le
conteneur en service directement, sans reconstruire l'image — bloqué au
moment du test par un problème réseau/certificat sans rapport avec
pgBackRest) ; activation du repo2 S3 cross-région quand des identifiants
cloud seront disponibles.

---

## 4. Vérifications post-restauration

| Vérification | Commande | Attendu |
|---|---|---|
| Tables | `SELECT count(*) FROM information_schema.tables WHERE table_schema='public'` | ≥ 116 |
| PostGIS | `SELECT PostGIS_Version()` | 3.4.x |
| AGE | `SELECT * FROM ag_catalog.cypher('gsie_knowledge_graph', $$ RETURN 1 $$) AS (a agtype)` | 1 |
| RLS | `SELECT count(*) FROM pg_class WHERE relrowsecurity` | ≥ 6 |
| Index FK | `SELECT count(*) FROM pg_indexes WHERE indexname LIKE 'idx_%'` | ≥ 110 |
| Migrations | `alembic current` | head |
| pg_stat_statements | `SELECT * FROM pg_available_extensions WHERE name='pg_stat_statements'` | installed |
| pgAudit | `SHOW shared_preload_libraries` | contient `pgaudit` |

---

## 5. RPO / RTO cibles

| Critère | Cible | Moyen |
|---|---|---|
| **RPO** (perte max) | ≤ 5 minutes | `archive_timeout=300` + incrémental 30 min |
| **RTO** (indispo max) | ≤ 15 minutes | standby hot + promotion manuelle |
| **Rétention** | 4 full + 2 diff | pgBackRest multi-repo |
| **Test restore** | trimestriel | `scripts/test_restore.sh` en CI |

---

## 6. Test de restauration trimestriel

```bash
# 1. Lancer un backup
./scripts/backup_pgdump.sh ./backups

# 2. Tester la restauration
./scripts/test_restore.sh ./backups/gsie_backup_$(date +%Y%m%d)_*.dump

# 3. Tracer le résultat dans 23_QUALITY_MANAGEMENT/AUDITS/
```

---

## 7. Streaming replication (standby hot)

### 7.1 Configuration primaire

```ini
# postgresql.conf
wal_level = replica
max_wal_senders = 6
archive_mode = on
archive_command = 'pgbackrest --stanza=gsie archive-push %p'
```

```ini
# pg_hba.conf — autoriser le standby à se répliquer
hostssl replication gsie_replicator <standby_ip>/32 scram-sha-256
```

```sql
CREATE ROLE gsie_replicator WITH LOGIN PASSWORD '...' REPLICATION;
```

### 7.2 Configuration standby

```ini
# postgresql.conf
hot_standby = on
```

```ini
# primary_conninfo (via recovery.signal ou postgresql.auto.conf)
primary_conninfo = 'host=<primary_ip> port=5432 user=gsie_replicator password=... sslmode=verify-full'
restore_command = 'pgbackrest --stanza=gsie archive-get %f %p'
```

### 7.3 Promotion manuelle (failover)

```bash
docker compose exec db-standby pg_ctl promote -D /var/lib/postgresql/data
```

> **Principe constitutionnel** : le failover est **manuel**.
> L'IA assiste, ne décide jamais.
