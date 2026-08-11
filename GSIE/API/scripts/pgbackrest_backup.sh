#!/usr/bin/env bash
# Sauvegarde pgBackRest GSIE — PITR (DEC-000037 P0-1, docs/BACKUP_RESTORE.md)
# Usage : ./scripts/pgbackrest_backup.sh [full|diff|incr]
#
# Déclenché depuis l'hôte (cron), exécute pgbackrest DANS le conteneur db
# via `docker exec` — pgbackrest et son dépôt (/var/lib/pgbackrest) vivent
# uniquement dans le conteneur/volume db, jamais sur l'hôte.
set -euo pipefail

BACKUP_TYPE="${1:-incr}"
CONTAINER="${GSIE_DB_CONTAINER:-api-db-1}"

case "$BACKUP_TYPE" in
  full|diff|incr) ;;
  *)
    echo "[pgbackrest] Usage: $0 [full|diff|incr]" >&2
    exit 1
    ;;
esac

echo "[pgbackrest] Backup ${BACKUP_TYPE} -> stanza gsie (conteneur ${CONTAINER})"
docker exec -u postgres "${CONTAINER}" pgbackrest --stanza=gsie --type="${BACKUP_TYPE}" backup

echo "[pgbackrest] Vérification post-backup"
docker exec -u postgres "${CONTAINER}" pgbackrest --stanza=gsie check

echo "[pgbackrest] État du dépôt"
docker exec -u postgres "${CONTAINER}" pgbackrest --stanza=gsie info
