#!/bin/sh
# entrypoint.sh — démarrage sans mutation implicite du schéma.
#
# Les migrations sont une opération explicite. Toute traversée de la révision
# irréversible 0005 exige une confirmation de backup et une autorisation
# destructive distinctes.
set -eu

if [ "${GSIE_RUN_MIGRATIONS_ON_STARTUP:-false}" = "true" ]; then
    current_revision="$(alembic current 2>/dev/null || true)"
    destructive_pending=true
    case "$current_revision" in
        *0005*|*0006*|*0007*|*0008*|*0009*|*0010*|*0011*|*0012*)
            destructive_pending=false
            ;;
    esac

    if [ "$destructive_pending" = "true" ]; then
        if [ "${GSIE_DATABASE_BACKUP_CONFIRMED:-false}" != "true" ] || \
           [ "${GSIE_ALLOW_DESTRUCTIVE_MIGRATIONS:-false}" != "true" ]; then
            echo "[entrypoint] REFUS: la migration 0005 peut supprimer les tables legacy." >&2
            echo "[entrypoint] Confirmer le backup ET l'autorisation destructive explicitement." >&2
            exit 78
        fi
    fi

    echo "[entrypoint] Lancement explicite des migrations Alembic..."
    alembic upgrade head
    echo "[entrypoint] Migrations terminées avec succès."
else
    echo "[entrypoint] Migrations automatiques désactivées (valeur sûre par défaut)."
fi

exec "$@"
