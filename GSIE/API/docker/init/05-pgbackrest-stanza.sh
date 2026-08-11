#!/bin/sh
# Initialise le dépôt WAL local avant l'arrêt du serveur initdb temporaire.
# Sans cette stanza, le premier archive-push sort en erreur 103 et PostgreSQL
# réinitialise ses processus en boucle malgré un conteneur encore « healthy ».
set -eu

echo "[init] Création et vérification de la stanza pgBackRest « gsie »..."
pgbackrest --stanza=gsie stanza-create
pgbackrest --stanza=gsie check
echo "[init] Stanza pgBackRest prête pour l'archivage WAL."
