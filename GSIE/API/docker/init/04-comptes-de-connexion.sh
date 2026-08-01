#!/bin/sh
# Crée les comptes de connexion applicatifs à l'initialisation du volume.
#
# Le SQL vit dans `docker/comptes-de-connexion.sql`, monté en lecture seule
# sur `/gsie/comptes-de-connexion.sql`. Ce script n'existe que pour lui
# passer les identifiants : les fichiers `.sql` déposés dans
# `docker-entrypoint-initdb.d` sont exécutés sans variables psql, et les
# mots de passe ne doivent ni être en dur, ni transiter par la ligne de
# commande d'un `CREATE ROLE` écrit à la main.
set -eu

: "${GSIE_API_DB_PASSWORD:?GSIE_API_DB_PASSWORD requis — voir GSIE/API/.env}"
: "${GSIE_VIZ_DB_PASSWORD:?GSIE_VIZ_DB_PASSWORD requis — voir GSIE/API/.env}"

api_user="${GSIE_API_DB_USER:-gsie_api}"
viz_user="${GSIE_VIZ_DB_USER:-gsie_viz}"

# Un mot de passe identique à celui de l'administrateur annulerait la
# séparation qu'on vient d'établir : le compte applicatif serait un alias du
# superutilisateur pour quiconque lit le `.env`.
if [ "$GSIE_API_DB_PASSWORD" = "${POSTGRES_PASSWORD:-}" ] ||
   [ "$GSIE_VIZ_DB_PASSWORD" = "${POSTGRES_PASSWORD:-}" ]; then
    echo "[init] REFUS: les comptes applicatifs doivent avoir un mot de passe" \
         "distinct de celui de l'administrateur." >&2
    exit 1
fi

echo "[init] Création des comptes de connexion « $api_user » et « $viz_user »..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v api_user="$api_user" \
    -v api_password="$GSIE_API_DB_PASSWORD" \
    -v viz_user="$viz_user" \
    -v viz_password="$GSIE_VIZ_DB_PASSWORD" \
    -v db_name="$POSTGRES_DB" \
    -f /gsie/comptes-de-connexion.sql

echo "[init] Comptes créés. Leurs droits sont accordés par la migration 20260801_0025."
