---
name: postgresql-postgis
description: Conventions PostgreSQL + PostGIS pour GSIE — schéma, requêtes géospatiales, migrations
triggers:
  - user
  - model
---

# PostgreSQL + PostGIS — Conventions GSIE

## Schéma référence

Voir `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` pour le schéma complet (PostgreSQL + Neo4j + ElasticSearch + Jena).

## Conventions de nommage

- Tables : `snake_case` pluriel (`forest_plots`, `evidence_records`)
- Colonnes géométriques : `geom` (SRID 4326 par défaut)
- Index géographiques : `idx_{table}_{colonne}_geom`
- Foreign keys : `fk_{table}_{ref_table}`
- Timestamps : `created_at`, `updated_at` (UTC, `TIMESTAMPTZ`)

## Colonne géométrique standard

```sql
ALTER TABLE forest_plots 
ADD COLUMN geom GEOMETRY(POINT, 4326);

CREATE INDEX idx_forest_plots_geom ON forest_plots USING GIST(geom);
```

## Requêtes géospatiales courantes

```sql
-- Points dans un rayon (km)
SELECT * FROM forest_plots
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography,
    radius_km * 1000
);

-- Intersection avec une zone (GeoJSON)
SELECT * FROM forest_plots
WHERE ST_Intersects(geom, ST_GeomFromGeoJSON('{"type":"Polygon",...}'));

-- Surface en hectares
SELECT ST_Area(geom::geography) / 10000 AS surface_ha FROM forest_zones;
```

## Utilisateurs DB — principe de moindre privilège

**Ne jamais connecter l'agent IA ou le MCP avec un compte superuser ou propriétaire du schéma.**

```sql
-- Utilisateur lecture seule pour le MCP Devin et les outils IA
CREATE USER gsie_readonly WITH PASSWORD 'mot_de_passe_fort';
GRANT CONNECT ON DATABASE gsie TO gsie_readonly;
GRANT USAGE ON SCHEMA public TO gsie_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO gsie_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO gsie_readonly;

-- Utilisateur applicatif (API GSIE uniquement) — lecture + écriture, jamais DDL
CREATE USER gsie_app WITH PASSWORD 'mot_de_passe_fort';
GRANT CONNECT ON DATABASE gsie TO gsie_app;
GRANT USAGE ON SCHEMA public TO gsie_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gsie_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gsie_app;

-- Jamais : GRANT ALL PRIVILEGES, SUPERUSER, CREATEDB sur gsie_app ou gsie_readonly
```

Configurer dans `.devin/config.local.json` :
```json
{
  "mcpServers": {
    "postgres": {
      "env": { "DATABASE_URL": "postgresql://gsie_readonly:...@localhost/gsie" }
    }
  }
}
```

## Connexion async (production — compte applicatif)

```python
import asyncpg

async def get_pool():
    # Utiliser gsie_app (jamais superuser) — DATABASE_URL depuis env
    return await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=30
    )
```

## Migrations

- Outil : Alembic
- Jamais de modification directe en prod
- Chaque migration = un fichier daté + description
- Toujours tester la migration inverse (`downgrade`)

## Performance

- Index sur toutes les FK et colonnes de filtre fréquent
- `EXPLAIN ANALYZE` avant tout requête complexe en prod
- VACUUM/ANALYZE sur les tables volumineuses
- PostGIS : préférer `ST_DWithin` à `ST_Distance` pour les recherches de proximité
