"""Resolution native d'une source : distribution -> scale_context.

NOMENCLATURE_SOURCES.md §8.1. L'inventaire recense ~179 sources dont la
resolution est decrite en prose (« Polygones 500 m2 min », « 50 cm rasters »,
« Placettes 20 m rayon »). Inexploitable par un moteur : deux sources ne sont
pas comparables tant que leur grain n'est pas un nombre.

Le metamodele portait deja `scale_context` avec `level`, `extent_m2`
(couverture) et `grain_m2` (resolution) — mais aucun `dataset`,
`distribution` ni `data_asset` ne le referencait. Quinze tables le font
(question, decision, correlation, scenario, sampling_event...), pas la chaine
des jeux de donnees. La resolution native d'une source n'avait donc aucun
emplacement.

Rattacher `distribution` a `scale_context` plutot qu'ajouter un
`native_grain_m2` evite de dupliquer la notion : deux sources de verite pour
une meme grandeur derivent tot ou tard, faute que DEC-000038 a precisement
ecartee pour les regles.

La colonne est NULLABLE : une distribution documentaire (publication, guide)
n'a pas de grain, et lui en inventer un serait une invention (ADR-009).
L'exigence porte a l'ecriture : une distribution qui DECLARE un
`scale_context` exige que celui-ci porte un `grain_m2`.

Revision ID: 20260728_0008
Revises: 20260728_0007
Create Date: 2026-07-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0008"
down_revision: str | None = "20260728_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "distribution"
_COLONNE = "scale_context_id"
_INDEX = "ix_distribution_scale_context_id"
_FK = "distribution_scale_context_id_fkey"


def upgrade() -> None:
    op.execute(f"ALTER TABLE {_TABLE} ADD COLUMN {_COLONNE} UUID")
    op.execute(
        f"ALTER TABLE {_TABLE} ADD CONSTRAINT {_FK} "
        f"FOREIGN KEY ({_COLONNE}) REFERENCES resource (id)"
    )
    op.execute(f"CREATE INDEX {_INDEX} ON {_TABLE} ({_COLONNE})")
    op.execute(
        f"COMMENT ON COLUMN {_TABLE}.{_COLONNE} IS "
        "'Resolution native de la source, via scale_context.grain_m2'"
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {_INDEX}")
    op.execute(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_FK}")
    op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN {_COLONNE}")
