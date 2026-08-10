"""Replace les enums Data Registry dans le schéma public.

La migration 0046 a été exécutée avec le ``search_path`` Docker
``ag_catalog,public,tiger``. Les deux enums qu'elle créait sans schéma
explicite ont donc atterri dans ``ag_catalog``. Ce schéma appartient à Apache
AGE et son usage n'est pas accordé au rôle applicatif ``gsie_api``. Les enums
du métamodèle vivent dans ``public`` : cette correction déplace uniquement
les deux types ajoutés par 0046, sans toucher aux données ni aux tables.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0047"
down_revision: str | None = "20260810_0046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENUMS = ("dataset_status", "dataset_health_status")


def _move_enum(source_schema: str, target_schema: str, name: str) -> None:
    """Déplace un enum s'il existe encore dans le schéma source."""

    # Les trois valeurs viennent uniquement des constantes ci-dessus ; elles
    # sont donc sûres à interpoler dans l'identifiant DDL (les paramètres
    # liés ne sont pas disponibles à l'intérieur d'un bloc PostgreSQL ``DO``).
    op.execute(
        sa.text(
            f"DO $$ BEGIN "
            f"IF EXISTS (SELECT 1 FROM pg_type t "
            f"JOIN pg_namespace n ON n.oid = t.typnamespace "
            f"WHERE t.typname = '{name}' AND n.nspname = '{source_schema}') THEN "
            f"EXECUTE 'ALTER TYPE {source_schema}.{name} SET SCHEMA {target_schema}'; "
            "END IF; END $$;"
        )
    )


def upgrade() -> None:
    for enum_name in _ENUMS:
        _move_enum("ag_catalog", "public", enum_name)


def downgrade() -> None:
    """Ne recrée jamais le défaut de schéma corrigé.

    La migration 0046 sait désormais supprimer explicitement les types dans
    ``public``. Les replacer dans ``ag_catalog`` rendrait son downgrade
    dépendant du search_path et réintroduirait un problème de privilèges.
    """
