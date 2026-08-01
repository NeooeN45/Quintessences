-- Comptes de connexion applicatifs — le superutilisateur cesse d'être le
-- compte d'exécution (audit sécurité 2026-08-01, constat A).
--
-- POSTGRES_USER est créé SUPERUSER et propriétaire de la base par l'image
-- officielle. Tant que l'API s'y connecte, rien de ce que construisent les
-- migrations 0004 et 0011→0023 ne s'applique : un superutilisateur ignore
-- les ACL et contourne RLS, `FORCE ROW LEVEL SECURITY` compris. L'isolement
-- de `gsie_rgpd_identites` — la table qui défait le pseudonymat — n'existait
-- donc que sur le papier.
--
-- Ce script crée les deux comptes de connexion qui manquaient :
--   * `gsie_api`  — exécution de l'API et du worker outbox ;
--   * `gsie_viz`  — outils de visualisation (Metabase, Superset, Dekart).
--
-- Il ne leur donne aucun droit ici : l'appartenance aux groupes
-- `gsie_application` et `gsie_viz_lecture` est accordée par la migration
-- 20260801_0025, ces groupes n'existant pas encore au moment de l'initdb.
-- Un compte créé ici sans migration ne peut donc rien lire — l'échec est
-- fermé, ce qui est la bonne direction.
--
-- Exécuté une seule fois, à la création du volume PostgreSQL. Pour une base
-- déjà initialisée, rejouer manuellement :
--   psql -U <admin> -d gsie -v api_user=gsie_api -v api_password="'...'" \
--        -v viz_user=gsie_viz -v viz_password="'...'" -v db_name=gsie \
--        -f 04-comptes-de-connexion.sql

\set ON_ERROR_STOP on

-- NOSUPERUSER NOBYPASSRLS : ce sont les deux attributs qui rendaient tout le
-- reste décoratif. NOCREATEDB NOCREATEROLE ferme l'escalade latérale.
CREATE ROLE :"api_user" LOGIN PASSWORD :'api_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
ALTER ROLE :"api_user" INHERIT;
GRANT CONNECT ON DATABASE :"db_name" TO :"api_user";
COMMENT ON ROLE :"api_user" IS
    'Compte d''execution de l''API et du worker. Membre de gsie_application '
    '(migration 20260801_0025) : noyau et domaines sans DELETE, aucun acces RGPD.';

CREATE ROLE :"viz_user" LOGIN PASSWORD :'viz_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
GRANT CONNECT ON DATABASE :"db_name" TO :"viz_user";
COMMENT ON ROLE :"viz_user" IS
    'Compte des outils de visualisation. Membre de gsie_viz_lecture '
    '(migration 20260801_0025) : SELECT seul, aucun acces aux schemas RGPD.';
