-- Rôles PostgreSQL GSIE — principe de moindre privilège (audit DB 2026-07-27 P0-4)
-- À exécuter une fois après l'initialisation de la base.
-- Le compte ${POSTGRES_USER} (superuser) reste pour l'admin uniquement.
--
-- Usage (psql, variables passées via -v) :
--   psql -U postgres -d gsie \
--     -v migrator_password="'<secret>'" \
--     -v app_password="'<secret>'" \
--     -v readonly_password="'<secret>'" \
--     -f init-roles.sql
--
-- Les mots de passe ne sont JAMAIS commités en clair — ils sont injectés
-- via des variables psql (:'password') lues depuis des secrets externes
-- (vault, .env non commité, secrets manager).

-- Rôle de migration (DDL uniquement — Alembic)
CREATE ROLE gsie_migrator WITH LOGIN PASSWORD :'migrator_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT ALL PRIVILEGES ON DATABASE gsie TO gsie_migrator;
GRANT CREATE ON SCHEMA public TO gsie_migrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gsie_migrator;

-- Rôle applicatif (DML uniquement — API FastAPI + worker)
CREATE ROLE gsie_app WITH LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE gsie TO gsie_app;
GRANT USAGE ON SCHEMA public TO gsie_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gsie_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gsie_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gsie_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO gsie_app;

-- Rôle lecture seule (MCP postgres + analyses)
CREATE ROLE gsie_readonly WITH LOGIN PASSWORD :'readonly_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE gsie TO gsie_readonly;
GRANT USAGE ON SCHEMA public TO gsie_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO gsie_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO gsie_readonly;

-- Révoquer les droits par défaut de PUBLIC
REVOKE ALL ON SCHEMA public FROM PUBLIC;
