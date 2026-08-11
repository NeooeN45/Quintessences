-- Audit trail PostgreSQL (audit sécurité 2026-07-27 P0-4) — pgAudit journalise
-- les DDL, écritures (write) et changements de rôles au niveau session/objet.
-- Exécuté automatiquement à la première initialisation du volume
-- (docker-entrypoint-initdb.d), après que shared_preload_libraries
-- (docker-compose.yml) a chargé la bibliothèque.
SET search_path = public, pg_catalog;
CREATE EXTENSION IF NOT EXISTS pgaudit;
