---
name: migration-db
description: Migration PostgreSQL/PostGIS sécurisée — Alembic, test upgrade+downgrade, rollback
argument-hint: "[description-migration]"
triggers:
  - user
  - model
---

# Migration DB GSIE — Alembic + PostGIS

## Principe absolu

> Jamais de modification directe en production.
> Chaque migration doit être testée dans les deux sens (upgrade + downgrade).
> Toujours backup avant migration en production.

## Processus

### 1. Créer la migration

```bash
cd GSIE/
alembic revision -m "description_courte_en_snake_case"
```

### 2. Écrire la migration

```python
"""description courte

Revision ID: abc123
Revises: previous_revision
Create Date: 2025-01-15
"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "abc123"
down_revision = "previous_revision"

def upgrade() -> None:
    # Ajouter colonne geom à forest_plots
    op.add_column(
        "forest_plots",
        sa.Column("geom", Geometry("POINT", srid=4326))
    )
    # Index GIST pour les requêtes spatiales
    op.execute(
        "CREATE INDEX idx_forest_plots_geom "
        "ON forest_plots USING GIST(geom)"
    )

def downgrade() -> None:
    op.drop_index("idx_forest_plots_geom", table_name="forest_plots")
    op.drop_column("forest_plots", "geom")
```

### 3. Tester la migration

```bash
# Upgrade
alembic upgrade head

# Vérifier le schéma
psql -c "\d forest_plots"

# Downgrade (CRITIQUE — doit marcher)
alembic downgrade -1

# Re-upgrade
alembic upgrade head
```

### 4. Règles PostGIS

- SRID 4326 (WGS84) par défaut pour toutes les colonnes geom
- Index GIST sur toutes les colonnes geom
- `ST_DWithin` pour proximité (pas `ST_Distance` + comparaison)
- `::geography` pour les calculs en mètres (pas en degrés)

### 5. Règles générales

- **Une migration = un changement conceptuel** (pas grouper plusieurs features)
- **Toujours implémenter downgrade** (sauf si impossible — alors documenter pourquoi)
- **Jamais DROP TABLE** sans vérifier qu'aucune FK ne référence
- **Jamais ALTER COLUMN** qui casse les données existantes sans migration de données
- **Tester sur un dump de prod** avant de déployer

### 6. Vérification finale

```bash
# Lint SQL
sqlfluff lint GSIE/migrations/

# Test d'intégrité
psql -c "SELECT postgis_full_version();"
psql -c "SELECT count(*) FROM forest_plots;"  # données préservées

# Tests applicatifs
pytest GSIE/tests/test_db/ -v
```

### 7. Documentation

- Entrée CHANGELOG.md : `feat(db): [description]`
- Si migration structurante → DEC-xxxxxx
- Mettre à jour `GSIE/ARCHITECTURE/ENCYCLOPEDIA_DATABASE_SCHEMA.md` si le schéma change
