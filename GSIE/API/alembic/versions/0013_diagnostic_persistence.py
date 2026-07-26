"""Migration 0013 — Persistance des diagnostics (type de resource `diagnostic`)

Ajoute un type de resource `diagnostic` et sa table satellite, pour que le
`diagnostic_id` produit par le Diagnostic Engine soit résolvable. Sans lui,
`RecommendationRequest` (`RECOMMENDATION_ENGINE.md` §5), qui prend un simple
`diagnostic_id` en entrée, ne peut résoudre aucun diagnostic.

Aucun type existant n'est réutilisé : `inference` désigne la prédiction d'un
modèle statistique, `recommendation` une recommandation générique portée par
un acteur, et `diagnostic_protocol` un protocole sanitaire (RFC-0016), donc
une méthode et non un résultat. Les confondre rendrait indistinguables en
base une conclusion tracée par règles explicites et une prédiction opaque
(`GSIE-CON-004`).

Crée trois enums PostgreSQL : `diagnostic_type`, `diagnostic_global_state`,
`diagnostic_validation_status`. Réutilise `evidence_level` (créé en 0002).

Rollback : DROP de la table `diagnostic` et des trois enums créés ici. Les
lignes `resource` de type `diagnostic` sont supprimées avec elle — la table
satellite en est la seule raison d'exister, et laisser des `resource`
orphelines rendrait citables des diagnostics dont le corps a disparu.
`evidence_level` n'est pas touché : il préexiste et sert à d'autres tables.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-26
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENUMS_CREES = (
    "diagnostic_type",
    "diagnostic_global_state",
    "diagnostic_validation_status",
)


def upgrade() -> None:
    from gsie_api.infrastructure.models import Base, diagnostic  # noqa: F401

    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=[diagnostic.DiagnosticModel.__table__],
    )


def downgrade() -> None:
    # Les lignes resource correspondantes disparaissent avec la table : sans
    # corps, un diagnostic resterait citable mais illisible.
    op.execute("DELETE FROM resource WHERE type = 'diagnostic'")
    op.drop_table("diagnostic")
    for nom in _ENUMS_CREES:
        op.execute(f"DROP TYPE IF EXISTS {nom}")
