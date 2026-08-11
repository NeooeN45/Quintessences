"""Ajoute le socle du Data Registry RFC-0038 (Phase 2).

Migration additive : les lignes historiques restent ``discovered`` et les
champs de qualification sont nullables jusqu'à leur reprise par manifeste.
Les tables satellites sont isolées dans ``gsie_gouvernance`` ; aucune donnée
RGPD existante n'est déplacée.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260810_0046"
down_revision: str | None = "20260810_0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DATASET_STATUS_VALUES = (
    "discovered",
    "link_checked",
    "metadata_extracted",
    "license_analyzed",
    "coverage_analyzed",
    "schema_analyzed",
    "security_checked",
    "validated",
    "staging",
    "production",
    "deprecated",
    "broken",
    "unavailable",
    "license_restricted",
    "unknown_license",
    "archived",
    "experimental",
)
_DATASET_HEALTH_VALUES = ("healthy", "degraded", "unavailable", "invalid", "unknown")


def _create_enum(name: str, values: tuple[str, ...]) -> None:
    # Le schéma est explicite : le search_path Docker commence par
    # ``ag_catalog`` pour Apache AGE et ne doit jamais décider où vivent les
    # types applicatifs.
    enum_type = postgresql.ENUM(*values, name=name, schema="public")
    enum_type.create(op.get_bind(), checkfirst=True)


def _drop_enum(name: str) -> None:
    postgresql.ENUM(name=name, schema="public").drop(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    _create_enum("dataset_status", _DATASET_STATUS_VALUES)
    _create_enum("dataset_health_status", _DATASET_HEALTH_VALUES)

    # Identité et vocabulaire du Dataset.
    op.add_column("dataset", sa.Column("slug", sa.String(length=200), nullable=True))
    op.add_column("dataset", sa.Column("primary_domain", sa.String(length=100), nullable=True))
    op.add_column("dataset", sa.Column("domains", postgresql.JSONB(), nullable=True))
    op.add_column("dataset", sa.Column("tags", postgresql.JSONB(), nullable=True))
    op.add_column(
        "dataset",
        sa.Column("domain_vocabulary_version", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_dataset_slug", "dataset", ["slug"], unique=False)
    op.create_index("ix_dataset_primary_domain", "dataset", ["primary_domain"], unique=False)
    op.create_unique_constraint("uq_dataset_slug", "dataset", ["slug"])

    # Qualification et couverture temporelle d'une publication.
    op.add_column(
        "dataset_version",
        sa.Column(
            "status",
            postgresql.ENUM(
                *_DATASET_STATUS_VALUES,
                name="dataset_status",
                schema="public",
                create_type=False,
            ),
            nullable=False,
            server_default="discovered",
        ),
    )
    op.alter_column("dataset_version", "status", server_default=None)
    op.add_column(
        "dataset_version",
        sa.Column("temporal_coverage_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "dataset_version",
        sa.Column("temporal_coverage_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("dataset_version", sa.Column("schema_hash", sa.String(length=128), nullable=True))
    op.add_column(
        "dataset_version",
        sa.Column(
            "evidence_level",
            postgresql.ENUM("A", "B", "C", "D", "E", "F", name="evidence_level", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("dataset_version", sa.Column("evidence_basis", postgresql.JSONB(), nullable=True))
    op.add_column(
        "dataset_version",
        sa.Column("evidence_assessed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dataset_version_status", "dataset_version", ["status"], unique=False)
    op.create_unique_constraint(
        "uq_dataset_version_dataset_version", "dataset_version", ["dataset_id", "version"]
    )
    op.create_check_constraint(
        "ck_dataset_version_coverage_order",
        "dataset_version",
        "temporal_coverage_start IS NULL OR temporal_coverage_end IS NULL "
        "OR temporal_coverage_start <= temporal_coverage_end",
    )

    # Projection de distribution ; les colonnes historiques sont conservées.
    op.add_column(
        "distribution",
        sa.Column("data_rights_statement_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "distribution",
        sa.Column("coverage_place_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("distribution", sa.Column("format", sa.String(length=50), nullable=True))
    op.add_column("distribution", sa.Column("crs", postgresql.JSONB(), nullable=True))
    op.create_index(
        "ix_distribution_data_rights_statement_id",
        "distribution",
        ["data_rights_statement_id"],
        unique=False,
    )
    op.create_index(
        "ix_distribution_coverage_place_id", "distribution", ["coverage_place_id"], unique=False
    )
    op.create_index("ix_distribution_format", "distribution", ["format"], unique=False)
    op.create_foreign_key(
        "fk_distribution_data_rights_statement",
        "distribution",
        "resource",
        ["data_rights_statement_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_distribution_coverage_place", "distribution", "resource", ["coverage_place_id"], ["id"]
    )
    # Permet au contrôle de santé d'imposer la cohérence conjointe
    # distribution_id → dataset_version_id (une distribution ne peut pas
    # être observée au travers d'une autre version).
    op.create_unique_constraint(
        "uq_distribution_id_dataset_version",
        "distribution",
        ["id", "dataset_version_id"],
    )

    # Droits de dataset : schéma gouvernance, jamais gsie_rgpd.
    op.create_table(
        "data_rights_statement",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resource.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("licence", sa.String(length=200), nullable=False),
        sa.Column(
            "usage_rights",
            postgresql.ENUM(
                "open", "restricted", "private", name="usage_rights", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "commercial_use_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "redistribution_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("attribution_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ai_training_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="gsie_gouvernance",
    )
    op.create_index(
        "ix_gsie_gouvernance_data_rights_statement_licence",
        "data_rights_statement",
        ["licence"],
        unique=False,
        schema="gsie_gouvernance",
    )

    # Historique des contrôles de santé, rattaché à une distribution.
    op.create_table(
        "dataset_health",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resource.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dataset_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("distribution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "health_status",
            postgresql.ENUM(
                *_DATASET_HEALTH_VALUES,
                name="dataset_health_status",
                schema="public",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_version", sa.String(length=200), nullable=True),
        sa.Column("schema_hash", sa.String(length=128), nullable=True),
        sa.Column("checksum_verified", sa.Boolean(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="ck_dataset_health_latency"
        ),
        sa.CheckConstraint(
            "http_status IS NULL OR (http_status >= 100 AND http_status <= 599)",
            name="ck_dataset_health_http_status",
        ),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["resource.id"]),
        sa.ForeignKeyConstraint(["distribution_id"], ["resource.id"]),
        sa.ForeignKeyConstraint(
            ["distribution_id", "dataset_version_id"],
            ["distribution.id", "distribution.dataset_version_id"],
            name="fk_dataset_health_distribution_version",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="gsie_gouvernance",
    )
    op.create_index(
        "ix_gsie_gouvernance_dataset_health_dataset_version_id",
        "dataset_health",
        ["dataset_version_id"],
        unique=False,
        schema="gsie_gouvernance",
    )
    op.create_index(
        "ix_gsie_gouvernance_dataset_health_distribution_id",
        "dataset_health",
        ["distribution_id"],
        unique=False,
        schema="gsie_gouvernance",
    )
    op.create_index(
        "ix_gsie_gouvernance_dataset_health_checked_at",
        "dataset_health",
        ["checked_at"],
        unique=False,
        schema="gsie_gouvernance",
    )
    op.create_index(
        "ix_gsie_gouvernance_dataset_health_health_status",
        "dataset_health",
        ["health_status"],
        unique=False,
        schema="gsie_gouvernance",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_gsie_gouvernance_dataset_health_health_status",
        table_name="dataset_health",
        schema="gsie_gouvernance",
    )
    op.drop_index(
        "ix_gsie_gouvernance_dataset_health_checked_at",
        table_name="dataset_health",
        schema="gsie_gouvernance",
    )
    op.drop_index(
        "ix_gsie_gouvernance_dataset_health_distribution_id",
        table_name="dataset_health",
        schema="gsie_gouvernance",
    )
    op.drop_index(
        "ix_gsie_gouvernance_dataset_health_dataset_version_id",
        table_name="dataset_health",
        schema="gsie_gouvernance",
    )
    op.drop_table("dataset_health", schema="gsie_gouvernance")
    op.drop_constraint("uq_distribution_id_dataset_version", "distribution", type_="unique")
    op.drop_index(
        "ix_gsie_gouvernance_data_rights_statement_licence",
        table_name="data_rights_statement",
        schema="gsie_gouvernance",
    )
    op.drop_table("data_rights_statement", schema="gsie_gouvernance")

    op.drop_constraint("fk_distribution_coverage_place", "distribution", type_="foreignkey")
    op.drop_constraint("fk_distribution_data_rights_statement", "distribution", type_="foreignkey")
    op.drop_index("ix_distribution_format", table_name="distribution")
    op.drop_index("ix_distribution_coverage_place_id", table_name="distribution")
    op.drop_index("ix_distribution_data_rights_statement_id", table_name="distribution")
    for column in ("crs", "format", "coverage_place_id", "data_rights_statement_id"):
        op.drop_column("distribution", column)

    op.drop_constraint("ck_dataset_version_coverage_order", "dataset_version", type_="check")
    op.drop_constraint("uq_dataset_version_dataset_version", "dataset_version", type_="unique")
    op.drop_index("ix_dataset_version_status", table_name="dataset_version")
    for column in (
        "evidence_assessed_at",
        "evidence_basis",
        "evidence_level",
        "schema_hash",
        "temporal_coverage_end",
        "temporal_coverage_start",
        "status",
    ):
        op.drop_column("dataset_version", column)

    op.drop_constraint("uq_dataset_slug", "dataset", type_="unique")
    op.drop_index("ix_dataset_primary_domain", table_name="dataset")
    op.drop_index("ix_dataset_slug", table_name="dataset")
    for column in (
        "domain_vocabulary_version",
        "tags",
        "domains",
        "primary_domain",
        "slug",
    ):
        op.drop_column("dataset", column)

    _drop_enum("dataset_health_status")
    _drop_enum("dataset_status")
