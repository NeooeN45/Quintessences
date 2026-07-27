# Runbook Disaster Recovery — Base de données GSIE

| Champ | Valeur |
|---|---|
| **ID** | DR-DB-001 |
| **Statut** | Draft |
| **Date** | 2026-07-27 |
| **Référence** | DEC-000037, DEC-000019, DEC-000036 |
| **Périmètre** | PostgreSQL 16 + PostGIS 3.4 + Apache AGE (116 tables) |

---

## 1. Objectifs RPO / RTO

| Critère | Cible | Moyen |
|---|---|---|
| **RPO** (perte max) | ≤ 5 minutes | `archive_timeout=300` + streaming replication |
| **RTO** (indisponibilité max) | ≤ 15 minutes | standby hot + promotion manuelle |
| **Rétention backups** | 4 full + 2 diff + incrémental | pgBackRest multi-repo (local + S3) |
| **Test de restauration** | trimestriel | `scripts/test_restore.sh` en CI |

> **Principe constitutionnel** : le failover est **manuel**. L'IA assiste,
> ne décide jamais. Aucun bascule automatique sans validation humaine.

---

## 2. Architecture cible

```
┌─────────────┐     streaming replication     ┌─────────────┐
│  Primary    │ ────────────────────────────► │   Standby   │
│  (rw)       │                               │   (hot, ro) │
└──────┬──────┘                               └──────┬──────┘
       │                                             │
       │  archive_command                            │
       ▼                                             │
┌─────────────┐                              ┌─────────────┐
│  pgBackRest │                              │  pgBackRest │
│  repo local │                              │  repo S3    │
│  (RTO court)│                              │  (DR long)  │
└─────────────┘                              └─────────────┘
```

---

## 3. Scénarios d'incident

### 3.1 Corruption logique (DROP accidentel, migration ratée)

**Détection** : erreur applicative, alerte monitoring, rapport utilisateur.

**Procédure** :
1. **STOP** — ne pas paniquer, ne pas relancer l'API.
2. Créer un restore point nommé AVANT l'incident si possible :
   ```sql
   SELECT pg_create_restore_point('avant_incident_20260727');
   ```
3. Identifier le timestamp cible (juste avant l'incident).
4. Arrêter l'API : `docker compose stop api outbox-worker`.
5. Restaurer via pgBackRest PITR :
   ```bash
   docker compose stop db
   pgbackrest --stanza=gsie --type=time \
     --target="2026-07-27 14:30:00+02" \
     --target-action=promote restore
   docker compose start db
   ```
6. Vérifier : `SELECT pg_is_in_recovery();` → doit retourner `false`.
7. Valider l'intégrité :
   ```bash
   ./scripts/test_restore.sh <backup_file>
   ```
   ou manuellement :
   ```sql
   SELECT count(*) FROM information_schema.tables WHERE table_schema='public';
   SELECT PostGIS_Version();
   SELECT * FROM ag_catalog.cypher('gsie_knowledge_graph', $$ RETURN 1 $$) AS (a agtype);
   ```
8. Redémarrer l'API : `docker compose start api outbox-worker`.
9. **Post-mortem** tracé dans `03_DECISIONS/`.

### 3.2 Perte du primaire (panne hardware, corruption disque)

**Détection** : alerte monitoring (primaire down > 60s), `pg_isready` échoue.

**Procédure** :
1. Confirmer la panne : `docker compose exec db pg_isready`.
2. **Décision humaine** de failover (pas d'automatisation).
3. Promouvoir le standby :
   ```bash
   docker compose exec db-standby pg_ctl promote -D /var/lib/postgresql/data
   ```
4. Reconfigurer PgBouncer vers le nouveau primaire (si PgBouncer actif) :
   ```bash
   docker compose exec pgbouncer pgbouncer -R /etc/pgbouncer/pgbouncer.ini
   ```
   ou via DNS : pointer `db` vers l'ancien standby.
5. Vérifier : `SELECT pg_is_in_recovery();` → `false`.
6. Reconstruire un nouveau standby depuis pgBackRest :
   ```bash
   pgbackrest --stanza=gsie --type=standby restore
   ```
7. Redémarrer l'API et valider.
8. **Post-mortem** tracé.

### 3.3 Perte de datacenter (DR géographique)

**Détection** : datacenter primaire injoignable.

**Procédure** :
1. Activer le standby cross-région (si configuré).
2. Promouvoir le standby cross-région.
3. Reconfigurer DNS / PgBouncer.
4. Restaurer depuis le repo pgBackRest S3 cross-région si pas de standby.
5. **Post-mortem** + RFC si l'architecture DR doit évoluer.

---

## 4. Procédure de backup

### 4.1 Backup manuel (quick win pg_dump)

```bash
./scripts/backup_pgdump.sh ./backups
```

### 4.2 Backup pgBackRest (cible)

```bash
# Full hebdomadaire (dimanche 01h00)
pgbackrest --stanza=gsie --type=full backup

# Diff quotidien (lundi-samedi 01h00)
pgbackrest --stanza=gsie --type=diff backup

# Incrémental toutes les 30 minutes
pgbackrest --stanza=gsie --type=incr backup

# Vérification quotidienne (06h00)
pgbackrest --stanza=gsie check
```

Cron recommandé :
```cron
0 1 * * 0 pgbackrest --stanza=gsie --type=full backup
0 1 * * 1-6 pgbackrest --stanza=gsie --type=diff backup
*/30 * * * * pgbackrest --stanza=gsie --type=incr backup
0 6 * * * pgbackrest --stanza=gsie check
```

---

## 5. Procédure de restauration

### 5.1 Restauration complète depuis pg_dump

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

### 5.2 PITR via pgBackRest

Voir §3.1 étape 5.

### 5.3 Vérifications post-restauration

| Vérification | Commande | Attendu |
|---|---|---|
| Tables | `SELECT count(*) FROM information_schema.tables WHERE table_schema='public'` | ≥ 116 |
| PostGIS | `SELECT PostGIS_Version()` | 3.4.x |
| AGE | `SELECT * FROM ag_catalog.cypher('gsie_knowledge_graph', $$ RETURN 1 $$) AS (a agtype)` | 1 |
| RLS | `SELECT count(*) FROM pg_class WHERE relrowsecurity` | ≥ 6 |
| Index FK | `SELECT count(*) FROM pg_indexes WHERE indexname LIKE 'idx_%'` | ≥ 110 |
| Migrations | `alembic current` | head |

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

## 7. Pré-requis de configuration

### 7.1 postgresql.conf

```ini
wal_level = replica
archive_mode = on
archive_command = 'pgbackrest --stanza=gsie archive-push %p'
archive_timeout = 300
max_wal_senders = 6
shared_preload_libraries = 'age,pg_stat_statements,pgaudit'
```

### 7.2 .env

```bash
GSIE_DB_PASSWORD=<strong_password>
GSIE_DB_SSL=require
GSIE_GUNICORN_WORKERS=5
```

---

## 8. Rôles et responsabilités

| Rôle | Responsabilité |
|---|---|
| **Fondateur** | Validation du failover, post-mortem |
| **DBA / Ops** | Exécution du runbook, monitoring |
| **IA (Devin)** | Détection, alerte, assistance — jamais décision de failover |

---

## 9. Historique des tests

| Date | Type | Résultat | Opérateur |
|---|---|---|---|
| 2026-07-27 | Création du runbook | — | Devin (GLM 5.2 High) |
| _à compléter_ | Premier test trimestriel | — | — |
