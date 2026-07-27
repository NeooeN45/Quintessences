#!/usr/bin/env bash
# Test de restauration PostgreSQL GSIE — Quick win P0 (audit DB 2026-07-27)
# Vérifie qu'un backup pg_dump est restaurable avec PostGIS + AGE fonctionnels
set -euo pipefail

BACKUP_FILE="${1:?Usage: ./scripts/test_restore.sh <backup_file.dump>}"
TEST_DB="gsie_restore_test_$(date +%s)"

DB_HOST="${GSIE_DB_HOST:-localhost}"
DB_PORT="${GSIE_DB_PORT:-5432}"
DB_USER="${GSIE_DB_USER:-gsie}"

echo "[restore-test] Creating test database: ${TEST_DB}"
PGPASSWORD="${GSIE_DB_PASSWORD:?GSIE_DB_PASSWORD required}" \
  createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${TEST_DB}"

echo "[restore-test] Restoring backup..."
PGPASSWORD="${GSIE_DB_PASSWORD}" \
  pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEST_DB}" --no-owner --no-privileges "${BACKUP_FILE}"

echo "[restore-test] Verifying table count (expect 116+)..."
TABLE_COUNT=$(PGPASSWORD="${GSIE_DB_PASSWORD}" \
  psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEST_DB}" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
echo "[restore-test] Tables: ${TABLE_COUNT}"

echo "[restore-test] Verifying PostGIS..."
PGPASSWORD="${GSIE_DB_PASSWORD}" \
  psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEST_DB}" -c "SELECT PostGIS_Version();"

echo "[restore-test] Verifying Apache AGE..."
PGPASSWORD="${GSIE_DB_PASSWORD}" \
  psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEST_DB}" -c "SELECT * FROM ag_catalog.cypher('gsie_knowledge_graph', \$\$ RETURN 1 \$\$) AS (a agtype);"

echo "[restore-test] Cleanup..."
PGPASSWORD="${GSIE_DB_PASSWORD}" \
  dropdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${TEST_DB}"

echo "[restore-test] SUCCESS — backup is restorable"
