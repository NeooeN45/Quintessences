# Audit Complet Base de Données GSIE — 2026-07-27

> Audit exhaustif du système de base de données, de la création à la sauvegarde.
> 5 sous-agents spécialisés (QA, backend/sécurité, SIG, architecte/DR) + analyse directe.
> Périmètre : `E:\Projets\Quintessences\GSIE\API` — PostgreSQL 16 + PostGIS 3.4 + Apache AGE, 116 tables, schéma v6.2.

---

## Score global

| Dimension | Score | Statut | Auditeur |
|---|---|---|---|
| Schéma & migrations Alembic | **72%** | 🟠 | QA |
| Sécurité DB | **57%** | 🟠 | Backend |
| PostGIS & performance | **35%** | 🔴 | SIG + analyse directe |
| Sauvegarde & recovery | **5%** | 🔴 | Architecte |
| Intégrité référentielle | **45%** | 🔴 | Analyse directe |
| **Score global pondéré** | **~43%** | 🔴 | — |

**Verdict** : Le socle applicatif (migrations, ORM, validation) est mature, mais **la couche infrastructure DB est quasi inexistante** — aucune sauvegarde, aucun durcissement PostgreSQL natif, 110 FK sans index, pas de RLS, pas de TLS. Le risque de perte de données totale est **critique et immédiat**.

---

## Problèmes P0 (bloquants — action immédiate requise)

### P0-1 — Aucune sauvegarde de la base de données
- **Impact** : Perte de données totale et irréversible en cas d'incident disque, `docker volume rm`, corruption, ou `DELETE`/`DROP` sans `WHERE`.
- **Preuve** : `grep "pg_dump|pg_basebackup|barman|pgbackrest|wal-g"` → 0 résultat dans tout le dépôt. Aucun cron, aucun script, aucun runbook.
- **RPO actuel** : ∞ (perte totale possible) · **RTO** : indéterminé.
- **Fichier** : `docker-compose.yml:32-33` (volume `gsie_pgdata` local, seul mécanisme de persistance).
- **Recommandation** : Script `pg_dump -Fc` quotidien immédiat + pgBackRest + archivage WAL → S3 (cf. plan d'action).

### P0-2 — Pool de connexions non borné vs `max_connections`
- **Impact** : `FATAL: too many connections` en production. Sur un hôte 8 cœurs : 17 workers Gunicorn × 15 connexions (pool 5 + overflow 10) = **255 connexions potentielles** vs `max_connections=100`.
- **Preuve** : `config.py:54-56` (commentaire faux "5 workers × 5 = 25"), `gunicorn.conf.py:9` (`cpu_count() * 2 + 1`, non borné par cgroups), `docker-compose.yml:29` (`max_connections=100`).
- **Recommandation** : Fixer `GUNICORN_WORKERS` via env var, recalculer `db_pool_size`/`db_max_overflow`, ou utiliser PgBouncer en mode transaction.

### P0-3 — 110 FK sur 323 sans index (47 tables concernées)
- **Impact** : Seq scans sur les tables cœur (`recommendation`, `correlation`, `assertion`, `flow`) dès que le volume dépasse quelques milliers de lignes.
- **Preuve** : Analyse programmatique — `recommendation` et `correlation` ont **0 index secondaire** malgré 5-6 FK chacune. Tables cœur de la chaîne Reasoning → Diagnostic → Recommendation.
- **Fichier** : `src/gsie_api/infrastructure/models/` (18 fichiers), `alembic/versions/20260726_0001_baseline_gsie_v6_2.py`.
- **Recommandation** : Migration Alembic dédiée ajoutant `CREATE INDEX` sur les 110 FK non indexées, en priorité `recommendation`, `correlation`, `assertion`, `flow`.

### P0-4 — Compte PostgreSQL unique superuser pour tout
- **Impact** : L'API, le worker, et les migrations utilisent toutes le même compte `gsie` (superuser). Une seule faille applicative = compromission totale de l'instance (DDL complet, création de rôles).
- **Preuve** : `docker-compose.yml:20-22` (`POSTGRES_USER: gsie` = superuser), `docker-compose.yml:94,145` (API + worker utilisent ce compte). Aucun `CREATE ROLE`/`GRANT`/`REVOKE` dans le dépôt.
- **CWE** : CWE-250 (moindre privilège non respecté).
- **Recommandation** : 3 rôles distincts — `gsie_migrator` (DDL, Alembic uniquement), `gsie_app` (DML only, API runtime), `gsie_readonly` (SELECT, MCP).

### P0-5 — Service `db` non durci dans Docker
- **Impact** : Un container compromis peut altérer/détruire les données sans contrainte OS. Contrairement à `api`/`outbox-worker`, le service `db` n'a pas `cap_drop: ALL` ni `read_only`.
- **Preuve** : `docker-compose.yml:15-47` — absence de `security_opt`/`cap_drop` sur le service `db`.
- **Recommandation** : Ajouter `security_opt: no-new-privileges:true`, `cap_drop: ALL` avec capabilities minimales PostgreSQL.

---

## Problèmes P1 (élevés — court terme)

### P1-1 — Aucune Row Level Security (RLS) sur les tables sensibles
- **Tables concernées** : `consent`, `data_subject` (RGPD), `sensitivity_classification`, `access_policy` (espèces protégées), `sample`, `observation` (GPS).
- **Impact** : Tout accès direct à la base (dump, MCP, worker compromis) contourne le RBAC applicatif.
- **CWE** : CWE-284.
- **Recommandation** : `ENABLE ROW LEVEL SECURITY` + politiques basées sur `SET app.current_user_roles` via variable de session.

### P1-2 — Champ `email_encrypted` non chiffré (trompeur)
- **Impact** : Donnée RGPD stockée en clair malgré un nom qui suggère un chiffrement.
- **Preuve** : `fair_rgpd.py:95` — `email_encrypted: Mapped[str | None] = mapped_column(String(500))`. Aucune fonction `Fernet`/`AES`/`pgcrypto` dans le code.
- **CWE** : CWE-311.
- **Recommandation** : Soit chiffrer réellement (Fernet + secret manager), soit renommer en `email` et tracer la dette.

### P1-3 — Aucun SSL/TLS sur la connexion PostgreSQL
- **Impact** : Trafic SQL (incluant credentials, données RGPD) en clair si API et DB ne sont pas sur le même segment isolé.
- **Preuve** : Aucun `sslmode`/`ssl=` dans `database.py` ou `config.py`. `validate_production_security` ne vérifie pas le TLS DB.
- **CWE** : CWE-319.
- **Recommandation** : `connect_args["ssl"] = "require"` en staging/production + garde dans `validate_production_security`.

### P1-4 — `compare_type`/`compare_server_default` non activés dans Alembic
- **Impact** : `alembic check` ne détecte pas les changements de type de colonne ou de valeur par défaut — dérive silencieuse possible.
- **Preuve** : `alembic/env.py:46-62` — `context.configure()` sans `compare_type=True`.
- **Recommandation** : Activer les deux options dans `env.py`.

### P1-5 — `_SCHEMA_FINGERPRINT` jamais vérifié
- **Impact** : Empreinte SHA-256 décorative qui suggère une garantie cryptographique inexistante.
- **Preuve** : `alembic/versions/20260726_0001_baseline_gsie_v6_2.py:24` — jamais recalculé ni comparé.
- **Recommandation** : Soit implémenter un test de non-régression (recalcul + assertion), soit retirer la mention.

### P1-6 — Absence quasi-totale de contraintes CHECK
- **Impact** : Intégrité métier reposant uniquement sur Pydantic — risque en cas d'écriture hors API (scripts, seeds, futurs services).
- **Preuve** : 8 `CHECK` seulement sur 116 tables, concentrées dans `forestry.py`. Aucun sur `confiance ∈ [0,1]`, `start_date <= end_date`, `area_ha >= 0`.
- **Recommandation** : Migration ajoutant `CHECK` sur les colonnes critiques (confiance, dates, grandeurs physiques).

### P1-7 — Aucun monitoring PostgreSQL natif
- **Impact** : Pas d'alerte sur espace disque, connexions, verrous, replication lag. Un incident de saturation serait détecté trop tard.
- **Preuve** : `pg_stat_statements` non activé dans `Dockerfile.db`. Prometheus existe côté API mais pas côté DB.
- **Recommandation** : Activer `pg_stat_statements` + `postgres_exporter` + dashboards Grafana + alertes.

### P1-8 — Aucun pgAudit
- **Impact** : Aucune trace de qui a fait quoi directement en base (hors ORM applicatif).
- **Preuve** : `grep "pgaudit"` → 0 résultat.
- **Recommandation** : `shared_preload_libraries = 'age,pgaudit,pg_stat_statements'` + `pgaudit.log = 'ddl, role, write'`.

### P1-9 — Single point of failure (instance DB unique)
- **Impact** : Panne du conteneur `db` ou de l'hôte = interruption totale pour l'API et toutes les apps clientes.
- **Preuve** : `docker-compose.yml` — 1 service `db`, pas de réplica, pas de failover.
- **Recommandation** : Streaming replication (1 standby asynchrone) dès passage multi-app.

### P1-10 — Aucun test de restauration de backup
- **Impact** : Même si un backup était créé, personne n'a vérifié qu'il est restaurable (PostGIS + AGE fonctionnels après restore).
- **Preuve** : `ci.yml` — aucun job backup/restore.
- **Recommandation** : Job CI hebdomadaire : backup → drop DB → restore → validation (count tables + requête PostGIS + requête Cypher AGE).

---

## Problèmes P2 (moyens — moyen terme)

| # | Problème | Fichier | Recommandation |
|---|---|---|---|
| P2-1 | Résidu `gsie_dev` dans l'historique git | commits `fb03766`, `21dee97` | Faire tourner le mot de passe si encore utilisé |
| P2-2 | `database_url` par défaut avec credentials en dur | `config.py:53` | Lever erreur si `GSIE_DATABASE_URL` absent |
| P2-3 | `alembic.ini` avec credentials en dur | `alembic.ini:7` | Remplacer par `CHANGE_ME` (écrasé par `env.py`) |
| P2-4 | Convention d'index incohérente (`ix_` × 220 vs `idx_` × 1) | baseline | Standardiser sur `idx_` |
| P2-5 | Aucune contrainte FK nommée explicitement | 323 FK | Nommer `fk_<table>_<col>` dans les futures migrations |
| P2-6 | Mode PgBouncer configuré mais non déployé | `config.py:61`, `docker-compose.yml` | Documenter ou retirer |
| P2-7 | `len(tables) == 116` — test par compte, pas par ensemble | `test_migration_contract.py:65` | Comparer les noms, pas le compte |
| P2-8 | Aucune documentation de schéma (ERD, dictionnaire) | — | Produire un ERD minimal pour 116 tables / 68 enums |
| P2-9 | Extensions non drop en downgrade non documenté | baseline docstring | Documenter le choix volontaire |
| P2-10 | Pas de validation de bornes GeoJSON | `engines/gis/engine.py:91` | Limiter vertices + valider type de géométrie |
| P2-11 | Pas de chiffrement at-rest du volume PostgreSQL | `docker-compose.yml:32` | Documenter l'exigence disque chiffré en prod |
| P2-12 | Pas de lien RGPD ↔ backups (droit à l'oubli) | — | Politique de rétention alignée RGPD |
| P2-13 | `str(exc)` potentiellement fuiteur de DSN dans logs | `app.py:130,140,153` | Masquer `://.*:.*@` avant logging |
| P2-14 | Comparaison password dev non constant-time | `auth/router.py:68` | `hmac.compare_digest()` |
| P2-15 | `pool_recycle` non configuré | `database.py` | Ajouter `pool_recycle=1800` |

---

## Synthèse par dimension

### 1. Schéma & migrations Alembic — 72% 🟠

**Points forts** :
- 116 tables, 68 enums, cohérence modèles ↔ migrations parfaite (vérifié programmatiquement)
- Réversibilité exemplaire : upgrade/downgrade symétriques, ordre FK respecté, testé réellement sur conteneur jetable
- Baseline autonome (SQL brut, pas d'import de modèles applicatifs)
- `validate_production_security` — garde-fou fail fast excellent
- Dockerfile.db durci (image épinglée par digest SHA-256, AGE compilé avec vérification hash)

**Points faibles** :
- 110 FK sans index (P0-3)
- `compare_type`/`compare_server_default` non activés (P1-4)
- `_SCHEMA_FINGERPRINT` décoratif (P1-5)
- 8 CHECK seulement sur 116 tables (P1-6)
- Pool sizing incohérent (P0-2)

### 2. Sécurité DB — 57% 🟠

**Points forts** :
- Injection SQL : **0 vulnérabilité** — usage discipliné de l'ORM SQLAlchemy (95%)
- Validation Pydantic aux frontières (90%)
- JWT RS256, RBAC centralisé, rate limiting
- `.env` jamais tracké, `.gitignore` correct

**Points faibles** :
- Compte unique superuser (P0-4)
- Aucune RLS (P1-1)
- `email_encrypted` non chiffré (P1-2)
- Pas de TLS DB (P1-3)
- Pas de pgAudit (P1-8)

### 3. PostGIS & performance — 35% 🔴

**Points forts** :
- SRID 2154 (Lambert-93) — bon choix pour calculs de surface en m² (forêt française)
- Index GIST présent sur `place.geometry`
- 1 colonne geom correctement typée

**Points faibles** :
- 110 FK sans index (P0-3) — impact performance majeur
- Type `GEOMETRY` générique (pas de contrainte de type géométrique)
- Pas de `ST_IsValid` sur les géométries entrantes
- Pas de partitionnement sur les tables volumineuses (observations, evidence)
- Pas de `pool_recycle`

### 4. Sauvegarde & recovery — 5% 🔴

**Points forts** :
- Volume Docker persistant nommé (`gsie_pgdata`)
- Redis AOF activé (mieux protégé que PostgreSQL — paradoxe)
- Cycle migration Alembic testé en CI

**Points faibles** :
- **Aucun backup** (P0-1) — score 0%
- Aucun PITR, aucun archivage WAL
- Aucun plan DR, aucun runbook, aucun RPO/RTO défini
- Aucun test de restauration (P1-10)
- Single point of failure (P1-9)

### 5. Intégrité référentielle — 45% 🔴

**Points forts** :
- 323 FK avec `ON DELETE CASCADE` cohérent (héritage par table via `resource`)
- Ordre topologique correct dans les migrations
- 68 enums typés (pas de VARCHAR)

**Points faibles** :
- 110 FK sans index (P0-3)
- 8 CHECK seulement (P1-6)
- Aucune FK nommée explicitement (P2-5)
- Aucun trigger d'audit
- Aucune contrainte de validité géométrique

---

## Plan d'action priorisé

### Quick wins (< 1 jour — arrêter l'hémorragie)

1. **Script `pg_dump -Fc` quotidien** — `GSIE/API/scripts/backup_pgdump.sh` + cron hôte
2. **Documenter la procédure de restore manuelle** — `GSIE/API/docs/BACKUP_RESTORE.md`
3. **Activer `wal_level=replica` explicitement** — `docker-compose.yml` command section
4. **Durcir le service `db`** — `security_opt`, `cap_drop: ALL` avec caps minimales
5. **Tester une restauration manuelle une fois** sur conteneur jetable

### Court terme (1-2 semaines)

6. **Migration Alembic : indexer les 110 FK** — en priorité `recommendation`, `correlation`, `assertion`, `flow`
7. **Créer 3 rôles PostgreSQL** (`gsie_migrator`, `gsie_app`, `gsie_readonly`) + `GRANT`/`REVOKE` explicites
8. **Activer RLS** sur `consent`, `data_subject`, `sensitivity_classification`, `access_policy`, `sample`, `observation`
9. **Décider : chiffrer `email_encrypted` ou renommer** — ne pas laisser un nom mensonger
10. **Ajouter `ssl=require`** sur `database_url` en staging/production + garde dans `validate_production_security`
11. **Activer `compare_type=True`/`compare_server_default=True`** dans `alembic/env.py`
12. **Corriger le pool sizing** — `GUNICORN_WORKERS` via env var, recalculer pool vs `max_connections`
13. **pgBackRest + archivage WAL** — `archive_mode=on`, `archive_command`, volume dédié
14. **Activer `pg_stat_statements` + `pgaudit`** — `shared_preload_libraries`
15. **Créer `DEC-xxxxxx`** — « Stratégie de sauvegarde et de reprise de la base GSIE »

### Moyen terme (1-3 mois)

16. **Migration : ajouter CHECK constraints** sur confiance ∈ [0,1], dates, grandeurs physiques
17. **Streaming replication** — 1 standby asynchrone
18. **`postgres_exporter` + Grafana** — dashboards connexions, locks, cache, WAL lag, backup status
19. **Test de restauration automatisé en CI** — job hebdomadaire backup → restore → validation
20. **Runbook DR** — `GSIE/API/docs/DISASTER_RECOVERY_RUNBOOK.md`
21. **Implémenter ou retirer `_SCHEMA_FINGERPRINT`**
22. **Documenter le schéma** — ERD minimal pour 116 tables

### Long terme (3-6 mois, production multi-app)

23. **Patroni + etcd** pour failover automatique
24. **PgBouncer en mode transaction** (HA)
25. **Backup off-site chiffré** (S3 / MinIO, AES-256)
26. **Drill DR trimestriel** documenté
27. **Politique de rétention RGPD-aligned** (7j + 4w + 12m + purge auto)

---

## Architecture cible recommandée

```
┌─────────────────────────────────────────────────────────────────┐
│  Hôte(s) de production                                          │
│                                                                   │
│  ┌──────────────┐     WAL streaming      ┌──────────────┐       │
│  │ PostgreSQL   │ ─────────────────────► │ PostgreSQL   │       │
│  │ primaire     │                        │ standby (RO) │       │
│  │ (PostGIS+AGE)│                        │              │       │
│  └──────┬───────┘                        └──────────────┘       │
│         │ archive_command                                       │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  pgBackRest  │  full hebdo + incr quotidien + WAL continu    │
│  └──────┬───────┘                                               │
└─────────┼─────────────────────────────────────────────────────────┘
          │ chiffré AES-256, compressé
          ▼
┌─────────────────────────┐
│  Stockage objet hors-site │  ← S3 / MinIO (réutilise ADR-006)
│  (rétention 7j/4w/12m)    │
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│  Job CI hebdomadaire      │  ← backup → restore → validation
│  (PostGIS + AGE + 116 t.) │
└─────────────────────────┘

Monitoring : postgres_exporter → Prometheus → Grafana → alertes
Rôles : gsie_migrator (DDL) / gsie_app (DML) / gsie_readonly (SELECT)
RLS : consent, data_subject, sensitivity_classification, access_policy, sample, observation
TLS : ssl=require sur toutes connexions DB
```

---

## Décision à tracer

**`DEC-xxxxxx` — « Stratégie de sauvegarde, sécurité et performance de la base GSIE »**
- Réfère à RFC-0021 (socle de fiabilité) comme tranche complémentaire.
- Comble l'angle mort de DEC-000031 (la « confirmation de sauvegarde » avant migration prod doit s'appuyer sur un mécanisme réel).
- Tranche : outil (pgBackRest), fréquence, RPO/RTO Phase 4, stockage (S3 ADR-006), rétention, rôles PostgreSQL, RLS, TLS.
- Impact contrats d'interface moteurs : **aucun** — préoccupation infrastructure transverse.

---

## Inventaire des fichiers audités

| Fichier | Rôle | Lignes clés |
|---|---|---|
| `docker-compose.yml` | Orchestration Docker | L.15-47: service DB, L.32-33: volume unique, L.29: max_connections=100 |
| `Dockerfile.db` | Image PG16+PostGIS+AGE | L.5: image épinglée digest, L.38: shared_preload_libraries |
| `alembic.ini` | Config migrations | L.7: credentials en dur (écrasés par env.py) |
| `alembic/env.py` | Env migrations async | L.27: get_settings(), L.46-62: manque compare_type |
| `alembic/versions/20260726_0001_baseline_gsie_v6_2.py` | Baseline 116 tables | L.24: fingerprint non vérifié, L.170: "constraint" quotée |
| `alembic/versions/20260726_0002_outbox_retry_dead_letter.py` | Révision outbox | Downgrade symétrique exact |
| `src/gsie_api/core/config.py` | Configuration | L.53: database_url défaut, L.54-56: pool sizing faux, L.127-152: validate_production_security |
| `src/gsie_api/infrastructure/database.py` | Engine SQLAlchemy | L.35-39: PgBouncer mode, L.56-67: get_db rollback |
| `src/gsie_api/infrastructure/models/` | 18 fichiers, 116 tables | 323 FK, 110 sans index, 8 CHECK, 1 colonne geom (SRID 2154) |
| `src/gsie_api/infrastructure/models/fair_rgpd.py` | Modèles RGPD | L.95: email_encrypted non chiffré |
| `src/gsie_api/infrastructure/models/spatial_temporal.py` | Modèle PostGIS | L.43-44: Geometry(GEOMETRY, 2154), index GIST |
| `tests/integration/test_migration_baseline.py` | Tests migration | Cycle up/down/up réel, alembic check |
| `tests/unit/test_migration_contract.py` | Contrats migration | L.65: len(tables)==116 (par compte) |
| `.github/workflows/ci.yml` | Pipeline CI | Aucun job backup/restore |
| `GSIE/ARCHITECTURE/ECOSYSTEM_METAMODEL.md` | Métamodèle v6.2 | L.1303: V3-9 Backup/restore identifié non implémenté |

---

## Conclusion

Le projet GSIE a un **socle applicatif mature** (migrations réversibles testées, ORM discipliné sans injection SQL, validation Pydantic, RBAC, JWT RS256, coverage 99%). Mais **la couche infrastructure DB est critique** :

- **Aucune sauvegarde** — risque de perte totale immédiate (P0 absolu)
- **Aucun durcissement PostgreSQL natif** — compte superuser unique, pas de RLS, pas de TLS, pas de pgAudit
- **110 FK sans index** — risque de performance sur les tables cœur de la chaîne métier
- **Pool sizing incohérent** — risque d'épuisement de connexions en production

Les quick wins (5 actions, < 1 jour) réduisent immédiatement le risque de perte totale. Le plan court terme (2 semaines) établit une stratégie de backup automatisée + PITR + durcissement sécurité + index FK. Le plan moyen terme (3 mois) atteint un niveau production-grade avec HA, monitoring et tests de restauration automatisés.

**Priorité absolue : exécuter les 5 quick wins avant toute autre fonctionnalité métier.**
