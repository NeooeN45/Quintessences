-- pgvector (recherche sémantique — migration 20260731_0024) — l'extension
-- est créée ici à l'initialisation du volume pour qu'elle soit disponible
-- immédiatement, même si alembic upgrade head n'a pas encore tourné.
-- La migration 20260731_0024 utilise CREATE EXTENSION IF NOT EXISTS, donc
-- cette création anticipée n'entre pas en conflit.
SET search_path = public, pg_catalog;
CREATE EXTENSION IF NOT EXISTS vector;
