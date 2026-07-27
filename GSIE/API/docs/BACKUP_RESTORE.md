# Sauvegarde et restauration PostgreSQL — GSIE

| Champ | Valeur |
|---|---|
| **ID** | DOC-BACKUP-001 |
| **Statut** | Draft |
| **Date** | 2026-07-27 |
| **Référence** | DEC-000037, DEC-000019 |
| **Périmètre** | PostgreSQL 16 + PostGIS 3.4 + Apache AGE (116 tables) |

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

```cron
# Full hebdomadaire (dimanche 01h00)
0 1 * * 0 pgbackrest --stanza=gsie --type=full backup

# Diff quotidien (lundi-samedi 01h00)
0 1 * * 1-6 pgbackrest --stanza=gsie --type=diff backup

# Incrémental toutes les 30 minutes
*/30 * * * * pgbackrest --stanza=gsie --type=incr backup

# Vérification quotidienne (06h00)
0 6 * * * pgbackrest --stanza=gsie check
```

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
