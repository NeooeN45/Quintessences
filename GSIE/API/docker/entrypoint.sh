#!/bin/sh
# entrypoint.sh — migrations Alembic puis démarrage de l'API
#
# Lance les migrations avant Gunicorn pour que le schéma DB soit à jour.
# En cas d'échec des migrations, l'API ne démarre pas (fail fast).
set -e

echo "[entrypoint] Lancement des migrations Alembic..."
alembic upgrade head
echo "[entrypoint] Migrations terminées avec succès."

# Exécuter la commande passée (CMD — Gunicorn)
exec "$@"
