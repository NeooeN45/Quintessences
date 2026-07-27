-- Monitoring PostgreSQL (P0-2) — active pg_stat_statements pour l'export
-- de métriques via postgres_exporter (voir docker/postgres-queries.yaml).
-- Exécuté automatiquement à la première initialisation du volume
-- (docker-entrypoint-initdb.d), après que shared_preload_libraries
-- (docker-compose.yml) a chargé la bibliothèque.
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
