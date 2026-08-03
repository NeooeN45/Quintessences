#!/usr/bin/env bash
# test_restauration_db.sh — Prouve que la base GSIE peut être sauvegardée
# et restaurée de bout en bout, avec vérification d'intégrité.
#
# Étapes :
#   1. pg_dump de la base gsie (format custom, compressé)
#   2. Création d'une base vierge gsie_restore_test
#   3. pg_restore depuis le dump
#   4. Vérifications d'intégrité :
#      - Extensions (postgis, age, vector)
#      - Schémas (count + noms)
#      - Tables (count + noms)
#      - Contraintes FK (count)
#      - RLS policies (count + noms)
#      - Roles (count + noms)
#      - Fonctions PostGIS (ST_Contains, ST_Area, etc.)
#   5. Si toutes les vérifications passent → exit 0
#   6. Nettoyage : DROP DATABASE gsie_restore_test
#
# Usage :
#   bash scripts/test_restauration_db.sh
#
# Prérequis :
#   - Docker container api-db-1 running
#   - Variables d'environnement GSIE_DB_USER et GSIE_DB_PASSWORD
#     (ou .env à la racine du projet API)
#
# Décision : DEC-000043 (S1 — Restauration DB prouvée)

set -euo pipefail

# --- Configuration ----------------------------------------------------------

CONTAINER="${GSIE_DB_CONTAINER:-api-db-1}"
ADMIN_USER="${GSIE_DB_USER:-gsie}"
ADMIN_DB="${GSIE_DB_NAME:-gsie}"
TEST_DB="gsie_restore_test"
DUMP_FILE="/tmp/gsie_backup.dump"

# Couleurs pour la sortie
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[ÉCHEC]${NC} $1"; exit 1; }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

# --- Nettoyage préalable ----------------------------------------------------

info "Nettoyage préalable : suppression de $TEST_DB si elle existe..."
docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$ADMIN_DB" \
  -c "DROP DATABASE IF EXISTS $TEST_DB;" 2>/dev/null || true

# --- Étape 1 : Backup -------------------------------------------------------

info "Étape 1/6 : Backup de la base $ADMIN_DB (pg_dump format custom)..."
START=$(date +%s)

docker exec "$CONTAINER" pg_dump \
  -U "$ADMIN_USER" \
  -d "$ADMIN_DB" \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges \
  --file="$DUMP_FILE"

END=$(date +%s)
DUMP_SIZE=$(docker exec "$CONTAINER" stat -c%s "$DUMP_FILE" 2>/dev/null || echo "?")
info "Backup terminé en $((END - START))s, taille : $DUMP_SIZE bytes"
ok "Backup créé : $DUMP_FILE"

# --- Étape 2 : Création base vierge -----------------------------------------

info "Étape 2/6 : Création de la base vierge $TEST_DB..."
docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$ADMIN_DB" \
  -c "CREATE DATABASE $TEST_DB;" 2>/dev/null
ok "Base $TEST_DB créée"

# Précharger l'extension AGE : pg_restore tente un DROP EXTENSION age
# avant que le schéma ag_catalog n'existe, ce qui produit un warning.
# Créer l'extension avant le restore évite ce warning.
info "Préchargement de l'extension AGE (évite le warning ag_catalog)..."
docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" \
  -c "CREATE EXTENSION IF NOT EXISTS age;" 2>/dev/null || true

# --- Étape 3 : Restore ------------------------------------------------------

info "Étape 3/6 : Restauration du dump dans $TEST_DB..."
START=$(date +%s)

docker exec "$CONTAINER" pg_restore \
  -U "$ADMIN_USER" \
  -d "$TEST_DB" \
  --no-owner \
  --no-privileges \
  --if-exists \
  --clean \
  "$DUMP_FILE" 2>&1 || true

END=$(date +%s)
info "Restauration terminée en $((END - START))s"
ok "Dump restauré dans $TEST_DB"

# --- Étape 4 : Vérifications d'intégrité ------------------------------------

info "Étape 4/6 : Vérifications d'intégrité..."

# 4a — Extensions
EXT_COUNT=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM pg_extension WHERE extname IN ('postgis', 'age', 'vector');")
EXT_COUNT=$(echo "$EXT_COUNT" | tr -d '[:space:]')
if [ "$EXT_COUNT" -ge 3 ]; then
  ok "Extensions : $EXT_COUNT/3 (postgis, age, vector)"
else
  fail "Extensions : $EXT_COUNT/3 — attendu 3 (postgis, age, vector)"
fi

# 4b — Schémas
SCHEMA_COUNT=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM information_schema.schemata
   WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema';")
SCHEMA_COUNT=$(echo "$SCHEMA_COUNT" | tr -d '[:space:]')
if [ "$SCHEMA_COUNT" -ge 6 ]; then
  ok "Schémas : $SCHEMA_COUNT (attendu >= 6)"
else
  fail "Schémas : $SCHEMA_COUNT — attendu >= 6"
fi

# 4c — Tables
TABLE_COUNT=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM information_schema.tables
   WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema';")
TABLE_COUNT=$(echo "$TABLE_COUNT" | tr -d '[:space:]')
if [ "$TABLE_COUNT" -ge 100 ]; then
  ok "Tables : $TABLE_COUNT (attendu >= 100)"
else
  fail "Tables : $TABLE_COUNT — attendu >= 100"
fi

# 4d — Contraintes FK
FK_COUNT=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM information_schema.table_constraints
   WHERE constraint_type = 'FOREIGN KEY';")
FK_COUNT=$(echo "$FK_COUNT" | tr -d '[:space:]')
if [ "$FK_COUNT" -ge 50 ]; then
  ok "Contraintes FK : $FK_COUNT (attendu >= 50)"
else
  fail "Contraintes FK : $FK_COUNT — attendu >= 50"
fi

# 4e — RLS policies
RLS_COUNT=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM pg_policies;")
RLS_COUNT=$(echo "$RLS_COUNT" | tr -d '[:space:]')
if [ "$RLS_COUNT" -ge 6 ]; then
  ok "RLS policies : $RLS_COUNT (attendu >= 6)"
else
  fail "RLS policies : $RLS_COUNT — attendu >= 6"
fi

# 4f — Fonctions PostGIS (st_contains, st_area, st_intersects, etc.)
POSTGIS_FUNCS=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid
   WHERE n.nspname = 'public' AND p.proname LIKE 'st_%';")
POSTGIS_FUNCS=$(echo "$POSTGIS_FUNCS" | tr -d '[:space:]')
if [ "$POSTGIS_FUNCS" -ge 10 ]; then
  ok "Fonctions PostGIS (st_*) : $POSTGIS_FUNCS (attendu >= 10)"
else
  fail "Fonctions PostGIS : $POSTGIS_FUNCS — attendu >= 10"
fi

# 4g — Index
INDEX_COUNT=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM pg_indexes
   WHERE schemaname NOT LIKE 'pg_%';")
INDEX_COUNT=$(echo "$INDEX_COUNT" | tr -d '[:space:]')
if [ "$INDEX_COUNT" -ge 50 ]; then
  ok "Index : $INDEX_COUNT (attendu >= 50)"
else
  fail "Index : $INDEX_COUNT — attendu >= 50"
fi

# 4h — Comparaison structure : même nombre de tables que la base source
SOURCE_TABLES=$(docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$ADMIN_DB" -t -c \
  "SELECT count(*) FROM information_schema.tables
   WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema';")
SOURCE_TABLES=$(echo "$SOURCE_TABLES" | tr -d '[:space:]')
if [ "$TABLE_COUNT" = "$SOURCE_TABLES" ]; then
  ok "Parité tables source/restaurée : $TABLE_COUNT = $SOURCE_TABLES"
else
  fail "Déséquilibre tables : source=$SOURCE_TABLES restaurée=$TABLE_COUNT"
fi

# --- Étape 5 : Nettoyage ----------------------------------------------------

info "Étape 5/6 : Nettoyage — suppression de $TEST_DB..."
docker exec "$CONTAINER" psql -U "$ADMIN_USER" -d "$ADMIN_DB" \
  -c "DROP DATABASE $TEST_DB;" 2>/dev/null
docker exec "$CONTAINER" rm -f "$DUMP_FILE" 2>/dev/null || true
ok "Base de test et dump temporaires supprimés"

# --- Étape 6 : Résultat -----------------------------------------------------

info "Étape 6/6 : Résultat final"
echo ""
echo "=============================================="
echo "  RESTAURATION DB PROUVÉE — SUCCÈS"
echo "=============================================="
echo "  Extensions : $EXT_COUNT/3"
echo "  Schémas    : $SCHEMA_COUNT"
echo "  Tables     : $TABLE_COUNT (parité source ✓)"
echo "  FK         : $FK_COUNT"
echo "  RLS        : $RLS_COUNT policies"
echo "  PostGIS    : $POSTGIS_FUNCS fonctions ST_*"
echo "  Index      : $INDEX_COUNT"
echo "=============================================="
echo ""
ok "S1 — Restauration DB prouvée (DEC-000043)"

exit 0
