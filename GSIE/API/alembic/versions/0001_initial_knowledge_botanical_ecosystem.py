"""Initial — Knowledge Engine + taxonomie botanique + écosystèmes + Apache AGE

Crée toutes les tables du schéma GSIE + les extensions PostgreSQL
(PostGIS, Apache AGE) + le graphe de connaissances AGE.

Revision ID: 0001
Revises:
Create Date: 2026-07-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Extensions PostgreSQL ---
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS age")
    op.execute("LOAD 'age'")
    op.execute("SET search_path = ag_catalog, public, tiger")

    # --- Graphe Apache AGE ---
    # Création du graphe de connaissances (KNOWLEDGE_GRAPH_SPECIFICATION.md)
    op.execute("SELECT create_graph('gsie_knowledge_graph')")

    # --- Tables : Knowledge Engine ---

    op.create_table(
        "knowledge_objects",
        sa.Column("connaissance_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("titre", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("domaine_scientifique", sa.String(50), nullable=False),
        sa.Column("contenu", postgresql.JSONB, nullable=False),
        sa.Column("evidence_level", sa.String(1), nullable=False),
        sa.Column("source", postgresql.JSONB, nullable=False),
        sa.Column("statut", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("date_integration", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("moteurs_consommateurs", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("evidence_level IN ('A', 'B', 'C', 'D', 'E', 'F')", name="ck_ko_evidence_level"),
        sa.CheckConstraint("statut IN ('accepte', 'quarantine', 'refuse')", name="ck_ko_statut"),
        sa.CheckConstraint(
            "type IN ('concept', 'relation', 'regle', 'seuil', 'modele', 'classification')",
            name="ck_ko_type",
        ),
    )
    op.create_index("ix_ko_type_evidence", "knowledge_objects", ["type", "evidence_level"])
    op.create_index("ix_ko_domaine_type", "knowledge_objects", ["domaine_scientifique", "type"])
    op.create_index("ix_knowledge_objects_type", "knowledge_objects", ["type"])
    op.create_index("ix_knowledge_objects_domaine_scientifique", "knowledge_objects", ["domaine_scientifique"])
    op.create_index("ix_knowledge_objects_evidence_level", "knowledge_objects", ["evidence_level"])

    op.create_table(
        "knowledge_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connaissance_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("rfc_reference", sa.String(50), nullable=True),
        sa.UniqueConstraint("connaissance_id", "version", name="uq_kh_connaissance_version"),
    )
    op.create_index("ix_knowledge_history_connaissance_id", "knowledge_history", ["connaissance_id"])

    op.create_table(
        "knowledge_domaines_validite",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connaissance_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"), nullable=False),
        sa.Column("parametre", sa.String(100), nullable=False),
        sa.Column("minimum", sa.Float(), nullable=True),
        sa.Column("maximum", sa.Float(), nullable=True),
        sa.Column("unite", sa.String(50), nullable=True),
    )
    op.create_index("ix_knowledge_domaines_validite_connaissance_id", "knowledge_domaines_validite", ["connaissance_id"])

    op.create_table(
        "knowledge_relations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connaissance_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"), nullable=False),
        sa.Column("cible_connaissance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("predicat", sa.String(100), nullable=False),
        sa.Column("sens", sa.String(20), nullable=False, server_default="sortant"),
        sa.CheckConstraint("sens IN ('sortant', 'entrant', 'bidirectionnel')", name="ck_kr_sens"),
    )
    op.create_index("ix_knowledge_relations_connaissance_id", "knowledge_relations", ["connaissance_id"])
    op.create_index("ix_knowledge_relations_cible_connaissance_id", "knowledge_relations", ["cible_connaissance_id"])

    op.create_table(
        "knowledge_mots_cles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connaissance_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"), nullable=False),
        sa.Column("mot_cle", sa.String(100), nullable=False),
        sa.UniqueConstraint("connaissance_id", "mot_cle", name="uq_kmc_connaissance_mot"),
    )
    op.create_index("ix_knowledge_mots_cles_connaissance_id", "knowledge_mots_cles", ["connaissance_id"])
    op.create_index("ix_knowledge_mots_cles_mot_cle", "knowledge_mots_cles", ["mot_cle"])

    op.create_table(
        "knowledge_conflits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connaissance_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_a", postgresql.JSONB, nullable=False),
        sa.Column("source_b", postgresql.JSONB, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_index("ix_knowledge_conflits_connaissance_id", "knowledge_conflits", ["connaissance_id"])

    # --- Tables : Taxonomie botanique ---

    op.create_table(
        "botanical_familles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nom_scientifique", sa.String(100), nullable=False, unique=True),
        sa.Column("nom_commun", sa.String(100), nullable=True),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "botanical_genres",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nom_scientifique", sa.String(100), nullable=False, unique=True),
        sa.Column("famille_id", sa.Integer(),
                  sa.ForeignKey("botanical_familles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_botanical_genres_famille_id", "botanical_genres", ["famille_id"])

    op.create_table(
        "botanical_essences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nom_scientifique", sa.String(150), nullable=False, unique=True),
        sa.Column("nom_vernaculaire", sa.String(100), nullable=False),
        sa.Column("genre_id", sa.Integer(),
                  sa.ForeignKey("botanical_genres.id", ondelete="CASCADE"), nullable=False),
        sa.Column("categorie_forestiere", sa.String(50), nullable=False),
        sa.Column("type_biologique", sa.String(50), nullable=True),
        sa.Column("aire_repartition", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("gbif_taxon_key", sa.Integer(), nullable=True),
        sa.Column("attributs", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_botanical_essences_nom_scientifique", "botanical_essences", ["nom_scientifique"])
    op.create_index("ix_botanical_essences_nom_vernaculaire", "botanical_essences", ["nom_vernaculaire"])
    op.create_index("ix_botanical_essences_genre_id", "botanical_essences", ["genre_id"])
    op.create_index("ix_botanical_essences_categorie_forestiere", "botanical_essences", ["categorie_forestiere"])
    op.create_index("ix_be_categorie_nom", "botanical_essences", ["categorie_forestiere", "nom_vernaculaire"])

    # --- Tables : Écosystèmes ---

    op.create_table(
        "ecosystem_habitats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code_eur28", sa.String(20), nullable=False, unique=True),
        sa.Column("nom_habitat", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("categorie", sa.String(100), nullable=False),
        sa.Column("interet_patrimonial", sa.String(50), nullable=True),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("attributs", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ecosystem_habitats_code_eur28", "ecosystem_habitats", ["code_eur28"])
    op.create_index("ix_ecosystem_habitats_categorie", "ecosystem_habitats", ["categorie"])

    op.create_table(
        "ecosystem_stations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code_station", sa.String(50), nullable=False, unique=True),
        sa.Column("nom_station", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("region_forestiere", sa.String(200), nullable=True),
        sa.Column("departements", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("altitude_min", sa.Integer(), nullable=True),
        sa.Column("altitude_max", sa.Integer(), nullable=True),
        sa.Column("ph_typique", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("rum_typique", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("essences_adaptees", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("essences_potentielles", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("attributs", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ecosystem_stations_code_station", "ecosystem_stations", ["code_station"])
    op.create_index("ix_ecosystem_stations_region_forestiere", "ecosystem_stations", ["region_forestiere"])

    op.create_table(
        "ecosystem_groupes_ecologiques",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nom_groupe", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("indicateur", sa.String(100), nullable=False),
        sa.Column("valeurs_indicatrices", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("especes_caracteristiques", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ecosystem_groupes_ecologiques_nom_groupe", "ecosystem_groupes_ecologiques", ["nom_groupe"])
    op.create_index("ix_ecosystem_groupes_ecologiques_indicateur", "ecosystem_groupes_ecologiques", ["indicateur"])


def downgrade() -> None:
    op.drop_table("ecosystem_groupes_ecologiques")
    op.drop_table("ecosystem_stations")
    op.drop_table("ecosystem_habitats")
    op.drop_table("botanical_essences")
    op.drop_table("botanical_genres")
    op.drop_table("botanical_familles")
    op.drop_table("knowledge_conflits")
    op.drop_table("knowledge_mots_cles")
    op.drop_table("knowledge_relations")
    op.drop_table("knowledge_domaines_validite")
    op.drop_table("knowledge_history")
    op.drop_table("knowledge_objects")

    # Supprimer le graphe AGE
    op.execute("SELECT drop_graph('gsie_knowledge_graph', true)")
