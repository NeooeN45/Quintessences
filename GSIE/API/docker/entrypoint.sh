#!/bin/sh
# entrypoint.sh — démarrage sans mutation implicite du schéma.
#
# Les migrations restent une opération explicite. La baseline 20260726_0001
# ne prend en charge que les bases neuves ou déjà rattachées à cette lignée.
set -eu

if [ "${GSIE_RUN_MIGRATIONS_ON_STARTUP:-false}" = "true" ]; then
    echo "[entrypoint] Vérification de la lignée Alembic..."
    if ! current_revision="$(alembic current 2>&1)"; then
        echo "[entrypoint] REFUS: historique Alembic absent ou incompatible." >&2
        printf '%s\n' "$current_revision" >&2
        echo "[entrypoint] Recréer la base locale ou exécuter une procédure de reprise validée." >&2
        exit 78
    fi

    if [ -n "$current_revision" ]; then
        echo "[entrypoint] Révision actuelle: $current_revision"
    else
        echo "[entrypoint] Base non versionnée: application de la baseline contrôlée."
    fi

    echo "[entrypoint] Lancement explicite des migrations Alembic..."
    alembic upgrade head
    echo "[entrypoint] Migrations terminées avec succès."
else
    echo "[entrypoint] Migrations automatiques désactivées (valeur sûre par défaut)."
fi

exec "$@"
