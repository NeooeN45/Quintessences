# DR-RESTAURATION — Procédure de sauvegarde et restauration DB GSIE

> **Décision** : DEC-000043 (S1 — Restauration DB prouvée)
> **Date** : 2026-08-02
> **Statut** : Validé — procédure testée et automatisée

## 1. Objectif

Prouver que la base GSIE (PostgreSQL 16 + PostGIS 3.4 + Apache AGE +
pgvector) peut être sauvegardée et restaurée de bout en bout, avec
vérification d'intégrité. Cette procédure est la première livrable de
la phase de stabilisation (DEC-000043).

## 2. Architecture DB

| Composant | Version | Rôle |
|---|---|---|
| PostgreSQL | 16.14 | Base relationnelle |
| PostGIS | 3.4.3 | Types géospatiaux, fonctions ST_* |
| Apache AGE | 1.5.0 | Traversées de graphe Cypher |
| pgvector | 0.8.5 | Embeddings vectoriels (1536 dims) |
| pgaudit | — | Audit SQL |

| Schéma | Tables | Rôle |
|---|---|---|
| `public` | 80+ | Tables transverses, métamodèle, junctions |
| `gsie_botanique` | 3 | Botanical Engine |
| `gsie_foret` | 10 | Forest Dynamics, schéma forestier RFC-0016 |
| `gsie_gouvernance` | 3 | Source registry, modèles |
| `gsie_climat` | 2 | Climate Engine |
| `gsie_pedologie` | 2 | Pedology Engine |
| `gsie_hydro` | 2 | Hydro Engine (stub) |
| `gsie_feu` | 2 | Ignis (stub) |
| `gsie_rgpd` | 3 | Tables RGPD (consent, access_policy) |
| `gsie_rgpd_identites` | 1 | data_subject (RGPD isolé) |

**Total** : 127 tables, 327 contraintes FK, 475 index, 6 RLS policies.

## 3. Procédure de sauvegarde

### 3.1. Backup manuel

```bash
# Depuis l'hôte, avec le conteneur Docker api-db-1 running
docker exec api-db-1 pg_dump \
  -U gsie \
  -d gsie \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges \
  --file=/tmp/gsie_backup.dump
```

**Format** : custom (binaire compressé) — permet le restore sélectif.

**Options** :
- `--no-owner` : les objets sont restaurés sans propriétaire (le
  propriétaire est déterminé par l'utilisateur de connexion au restore)
- `--no-privileges` : les GRANT/REVOKE ne sont pas inclus (recréés par
  les migrations)
- `--compress=9` : compression maximale

### 3.2. Backup automatisé (recommandé pour production)

```bash
# Cron quotidien (2h00) avec retention 30 jours
0 2 * * * docker exec api-db-1 pg_dump -U gsie -d gsie \
  --format=custom --compress=9 --no-owner --no-privileges \
  --file=/backups/gsie_$(date +\%Y\%m\%d).dump

# Nettoyage des backups > 30 jours
0 3 * * * find /backups -name "gsie_*.dump" -mtime +30 -delete
```

**TODO (P0-1)** : pgBackRest + WAL archiving pour PITR (Point-In-Time
Recovery). Le backup pg_dump est un snapshot — pas un PITR.

## 4. Procédure de restauration

### 4.1. Restauration manuelle

```bash
# 1. Créer une base vierge
docker exec api-db-1 psql -U gsie -d gsie \
  -c "CREATE DATABASE gsie_restore;"

# 2. Précharger AGE (évite le warning ag_catalog)
docker exec api-db-1 psql -U gsie -d gsie_restore \
  -c "CREATE EXTENSION IF NOT EXISTS age;"

# 3. Restaurer le dump
docker exec api-db-1 pg_restore \
  -U gsie \
  -d gsie_restore \
  --no-owner \
  --no-privileges \
  --if-exists \
  --clean \
  /tmp/gsie_backup.dump

# 4. Vérifier (voir §5)
```

### 4.2. Test automatisé

```bash
# Script bash (quick check)
bash scripts/test_restauration_db.sh

# Test Python (CI — testcontainers)
.\.venv\Scripts\python.exe -m pytest tests/integration/test_restauration_db.py -v --no-cov -n 0
```

## 5. Vérifications d'intégrité

Le test automatisé vérifie :

| Vérification | Requête | Seuil | Résultat mesuré |
|---|---|---|---|
| Extensions | `pg_extension WHERE extname IN ('postgis','age','vector')` | 3 | 3 ✓ |
| Schémas | `information_schema.schemata` (excluant pg_*) | ≥ 6 | 12 ✓ |
| Tables | `information_schema.tables` (excluant pg_*) | ≥ 100 | 127 ✓ |
| Contraintes FK | `table_constraints WHERE type='FOREIGN KEY'` | ≥ 50 | 327 ✓ |
| RLS policies | `pg_policies` | ≥ 6 | 6 ✓ |
| Fonctions PostGIS | `pg_proc WHERE proname LIKE 'st_%'` | ≥ 10 | 464 ✓ |
| Index | `pg_indexes` (excluant pg_*) | ≥ 50 | 475 ✓ |
| Parité tables | source vs restaurée | égalité | 127 = 127 ✓ |
| Parité FK | source vs restaurée | égalité | 327 = 327 ✓ |
| Parité index | source vs restaurée | égalité | 475 = 475 ✓ |
| ST_Area | `POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))` | = 1.0 | 1.0 ✓ |
| ST_Contains | polygone contient point | = true | true ✓ |
| ST_Distance | `POINT(0 0)` → `POINT(3 4)` | = 5.0 | 5.0 ✓ |

## 6. Performance mesurée

| Opération | Temps | Taille |
|---|---|---|
| Backup (pg_dump) | < 1s | 781 KB (schéma seul, 0 lignes) |
| Restore (pg_restore) | ~5s | — |
| Test complet (bash) | ~10s | — |
| Test complet (Python) | ~17s | — |

> Ces mesures sont sur une base vide (schéma seulement). Avec des
> données réelles (S2 — tranche verticale), les temps augmenteront.
> Le benchmark avec données sera mesuré pendant S3.

## 7. Notes techniques

### 7.1. Warning ag_catalog

`pg_restore` produit un warning si l'extension AGE n'est pas préchargée
avant le restore :

```
pg_restore: error: could not execute query: ERROR: schema "ag_catalog" does not exist
Command was: DROP EXTENSION IF EXISTS age;
```

**Solution** : créer l'extension AGE avant le restore (étape 2.2 ci-dessus).
L'extension est restaurée correctement (3/3) — le warning est uniquement
un problème d'ordre d'exécution.

### 7.2. Rôles et privilèges

Le backup utilise `--no-owner --no-privileges` : les rôles et GRANT ne
sont pas dans le dump. Ils sont recréés par :
- Les scripts d'initdb (`docker/comptes-de-connexion.sql`)
- La migration `20260801_0025` (rôles applicatifs)
- Les migrations `20260728_0011` à `0023` (schémas RGPD isolés)

**Restauration des rôles** : après restore, exécuter les migrations
Alembic sur la base restaurée pour recréer les rôles :

```bash
docker exec api-api-1 alembic upgrade head
```

### 7.3. Base vide vs base avec données

La base actuelle est vide (0 lignes) — seul le schéma est sauvegardé.
Quand S2 (tranche verticale) ingérera des données réelles, le test de
restauration devra vérifier :
- Row counts par table (parité source/restaurée)
- Intégrité référentielle (pas d'FK cassées)
- Géométries PostGIS valides (ST_IsValid)
- Données RGPD isolées (RLS active et fonctionnelle)

## 8. Fichiers

| Fichier | Rôle |
|---|---|
| `scripts/test_restauration_db.sh` | Script bash de test (quick check) |
| `tests/integration/test_restauration_db.py` | Test Python (CI, testcontainers) |
| `GSIE/DOCUMENTATION/DR-RESTAURATION.md` | Ce document |

## 9. Prochaines étapes

- **P0-1** : pgBackRest + WAL archiving pour PITR
- **S2** : Tranche verticale réelle avec données → retest avec row counts
- **CI** : Ajouter `test_restauration_db.py` au pipeline CI
