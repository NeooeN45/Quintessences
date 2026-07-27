#!/usr/bin/env bash
# Backup PostgreSQL GSIE — Quick win P0 (audit DB 2026-07-27)
# Usage : ./scripts/backup_pgdump.sh [output_dir]
set -euo pipefail

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${OUTPUT_DIR}/gsie_backup_${TIMESTAMP}.dump"

DB_HOST="${GSIE_DB_HOST:-localhost}"
DB_PORT="${GSIE_DB_PORT:-5432}"
DB_USER="${GSIE_DB_USER:-gsie}"
DB_NAME="${GSIE_DB_NAME:-gsie}"

mkdir -p "${OUTPUT_DIR}"

echo "[backup] Starting pg_dump -> ${BACKUP_FILE}"
PGPASSWORD="${GSIE_DB_PASSWORD:?GSIE_DB_PASSWORD required}" \
  pg_dump -Fc -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" \
  > "${BACKUP_FILE}"

echo "[backup] Done: $(du -h "${BACKUP_FILE}" | cut -f1)"

# Rotation : garder 7 derniers backups
ls -t "${OUTPUT_DIR}"/gsie_backup_*.dump | tail -n +8 | xargs -r rm --
echo "[backup] Rotation: 7 most recent backups retained"
