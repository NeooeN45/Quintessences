"""PostGIS -- validation geometrique et contraintes (audit DB 2026-07-27).

- Contrainte CHECK ST_IsValid sur place.geometry -- aucune geometrie
  invalide ne doit pouvoir etre persistee (GSIE-CON-005 : tracabilite
  et fiabilite des donnees geospatiales).
- Trigger BEFORE INSERT/UPDATE pour auto-reparation ST_MakeValid --
  repare les auto-intersections/anneaux mal formes issues de sources
  externes (API Carto, imports LiDAR/BD Foret) avant persistance.
- Colonne generee `geom_4326` (WGS84) pour l'interop GeoJSON/API sans
  dupliquer la logique de reprojection cote applicatif -- le SRID de
  stockage/calcul reste 2154 (Lambert-93).

Revision ID: 20260727_0005
Revises: 20260727_0004
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0005"
down_revision: str | None = "20260727_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "place"
_CHECK_CONSTRAINT = "chk_place_geometry_valid"
_TRIGGER_FUNCTION = "fn_validate_place_geometry"
_TRIGGER = "trg_validate_place_geometry"
_GEOM_4326_COLUMN = "geom_4326"
_GEOM_4326_INDEX = "idx_place_geom_4326"


def upgrade() -> None:
    # 1. Contrainte CHECK -- une geometrie invalide ne doit jamais etre
    # visible en base, meme si un appelant contourne le trigger via un
    # chemin d'ecriture SQL brut (COPY, migration de donnees, etc.).
    op.execute(
        f"ALTER TABLE {_TABLE} "
        f"ADD CONSTRAINT {_CHECK_CONSTRAINT} "
        f"CHECK (geometry IS NULL OR ST_IsValid(geometry))"
    )

    # 2. Fonction + trigger de reparation automatique -- repare les
    # geometries recuperables (ST_MakeValid) avant qu'elles n'atteignent
    # la contrainte CHECK, et rejette explicitement les geometries vides
    # qui ne portent aucune information spatiale exploitable.
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_TRIGGER_FUNCTION}() RETURNS trigger AS $$
        BEGIN
          IF NEW.geometry IS NOT NULL THEN
            IF NOT ST_IsValid(NEW.geometry) THEN
              NEW.geometry := ST_MakeValid(NEW.geometry);
            END IF;
            IF ST_IsEmpty(NEW.geometry) THEN
              RAISE EXCEPTION 'Geometrie vide non autorisee sur place.geometry';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER {_TRIGGER}
          BEFORE INSERT OR UPDATE OF geometry ON {_TABLE}
          FOR EACH ROW EXECUTE FUNCTION {_TRIGGER_FUNCTION}();
        """
    )

    # 3. Colonne generee WGS84 pour interop GeoJSON/API externes --
    # calculee par PostgreSQL (STORED), jamais par l'applicatif, pour
    # garantir qu'elle reste toujours synchronisee avec `geometry`.
    op.execute(
        f"ALTER TABLE {_TABLE} ADD COLUMN {_GEOM_4326_COLUMN} geometry(GEOMETRY, 4326) "
        f"GENERATED ALWAYS AS (ST_Transform(geometry, 4326)) STORED"
    )
    op.execute(
        f"CREATE INDEX {_GEOM_4326_INDEX} ON {_TABLE} USING GIST ({_GEOM_4326_COLUMN})"
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {_GEOM_4326_INDEX}")
    op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN IF EXISTS {_GEOM_4326_COLUMN}")
    op.execute(f"DROP TRIGGER IF EXISTS {_TRIGGER} ON {_TABLE}")
    op.execute(f"DROP FUNCTION IF EXISTS {_TRIGGER_FUNCTION}()")
    op.execute(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_CHECK_CONSTRAINT}")
