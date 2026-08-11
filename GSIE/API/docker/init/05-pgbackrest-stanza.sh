#!/bin/sh
# Initialise le dépôt WAL local avant l'arrêt du serveur initdb temporaire.
# Sans cette stanza, le premier archive-push sort en erreur 103 et PostgreSQL
# réinitialise ses processus en boucle malgré un conteneur encore « healthy ».
set -eu

archive_mode="$(
    psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
        --tuples-only --no-align --command 'SHOW archive_mode'
)"
if [ "$archive_mode" != "on" ]; then
    echo "[init] Archivage WAL désactivé : initialisation pgBackRest ignorée."
    return 0 2>/dev/null || exit 0
fi

: "${PGBACKREST_REPO1_CIPHER_PASS:?Passphrase pgBackRest requise avec archive_mode=on}"

echo "[init] Création et vérification de la stanza pgBackRest « gsie »..."
pgbackrest --stanza=gsie stanza-create
pgbackrest --stanza=gsie check
echo "[init] Stanza pgBackRest prête pour l'archivage WAL."
