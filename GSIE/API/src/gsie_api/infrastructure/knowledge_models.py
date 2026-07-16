"""Modèles SQLAlchemy — Knowledge Engine + taxonomie botanique + écosystèmes.

Schéma relationnel PostgreSQL pour la persistance du Knowledge Engine.
Le graphe de connaissances (Apache AGE) est une projection de ces tables
pour les requêtes de traversée Cypher.

Tables :
- knowledge_objects : KnowledgeObject (nœud central, versionné CON-010)
- knowledge_history : VersionEntry (historique immuable)
- knowledge_domaines_validite : DomaineValidite (conditions d'application)
- knowledge_relations : RelationRef (liens entre connaissances)
- knowledge_mots_cles : mots-clés (many-to-many)
- knowledge_conflits : ConflitBibliographique (S-3)

Taxonomie botanique (Phase 2) :
- botanical_familles : familles botaniques
- botanical_genres : genres botaniques
- botanical_essences : espèces (nom scientifique + vernaculaire)

Écosystèmes (Phase 4) :
- ecosystem_habitats : habitats Natura 2000 (EUR28)
- ecosystem_stations : types de stations forestières
- ecosystem_groupes_ecologiques : groupes écologiques (bio-indicateurs)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gsie_api.infrastructure.models import Base, TimestampMixin


class KnowledgeObjectModel(Base, TimestampMixin):
    """KnowledgeObject — nœud de connaissance versionné (CON-010).

    Source unique de vérité pour tous les moteurs de raisonnement.
    Chaque révision crée une nouvelle version (le champ version est incrémenté)
    et l'ancienne version est archivée dans knowledge_history.
    """

    __tablename__ = "knowledge_objects"

    # Identité
    connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Classification
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    titre: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    domaine_scientifique: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Contenu typé (JSONB — structure libre selon le type)
    contenu: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Preuve et source (CON-002, S-1, S-2)
    evidence_level: Mapped[str] = mapped_column(String(1), nullable=False, index=True)
    source: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False)

    # Versionnement (CON-010)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    date_integration: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("now()"),
    )

    # Métadonnées optionnelles (JSONB pour flexibilité)
    moteurs_consommateurs: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    # Relations
    history_entries: Mapped[list["KnowledgeHistoryModel"]] = relationship(
        back_populates="knowledge_object",
        cascade="all, delete-orphan",
        order_by="KnowledgeHistoryModel.version",
    )
    domaines_validite: Mapped[list["KnowledgeDomaineValiditeModel"]] = relationship(
        back_populates="knowledge_object",
        cascade="all, delete-orphan",
    )
    relations_refs: Mapped[list["KnowledgeRelationModel"]] = relationship(
        back_populates="knowledge_object",
        cascade="all, delete-orphan",
    )
    mots_cles: Mapped[list["KnowledgeMotCleModel"]] = relationship(
        back_populates="knowledge_object",
        cascade="all, delete-orphan",
    )
    conflits: Mapped[list["KnowledgeConflitModel"]] = relationship(
        back_populates="knowledge_object",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_ko_type_evidence", "type", "evidence_level"),
        Index("ix_ko_domaine_type", "domaine_scientifique", "type"),
        CheckConstraint(
            "evidence_level IN ('A', 'B', 'C', 'D', 'E', 'F')", name="ck_ko_evidence_level"
        ),
        CheckConstraint("statut IN ('accepte', 'quarantine', 'refuse')", name="ck_ko_statut"),
        CheckConstraint(
            "type IN ('concept', 'relation', 'regle', 'seuil', 'modele', 'classification')",
            name="ck_ko_type",
        ),
    )


class KnowledgeHistoryModel(Base):
    """Historique de version (CON-010 — aucune connaissance supprimée silencieusement).

    Chaque entrée archive une version antérieure avec sa justification.
    L'historique est immuable : on ne fait qu'ajouter des entrées.
    """

    __tablename__ = "knowledge_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    rfc_reference: Mapped[str | None] = mapped_column(String(50), nullable=True)

    knowledge_object: Mapped[KnowledgeObjectModel] = relationship(back_populates="history_entries")

    __table_args__ = (
        UniqueConstraint("connaissance_id", "version", name="uq_kh_connaissance_version"),
    )


class KnowledgeDomaineValiditeModel(Base):
    """Domaine de validité — conditions d'application d'une connaissance."""

    __tablename__ = "knowledge_domaines_validite"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parametre: Mapped[str] = mapped_column(String(100), nullable=False)
    minimum: Mapped[float | None] = mapped_column(nullable=True)
    maximum: Mapped[float | None] = mapped_column(nullable=True)
    unite: Mapped[str | None] = mapped_column(String(50), nullable=True)

    knowledge_object: Mapped[KnowledgeObjectModel] = relationship(
        back_populates="domaines_validite"
    )


class KnowledgeRelationModel(Base):
    """Référence vers une autre connaissance (graphe)."""

    __tablename__ = "knowledge_relations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cible_connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    predicat: Mapped[str] = mapped_column(String(100), nullable=False)
    sens: Mapped[str] = mapped_column(String(20), nullable=False, default="sortant")

    knowledge_object: Mapped[KnowledgeObjectModel] = relationship(back_populates="relations_refs")

    __table_args__ = (
        CheckConstraint("sens IN ('sortant', 'entrant', 'bidirectionnel')", name="ck_kr_sens"),
    )


class KnowledgeMotCleModel(Base):
    """Mot-clé pour la recherche (many-to-many)."""

    __tablename__ = "knowledge_mots_cles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mot_cle: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    knowledge_object: Mapped[KnowledgeObjectModel] = relationship(back_populates="mots_cles")

    __table_args__ = (
        UniqueConstraint("connaissance_id", "mot_cle", name="uq_kmc_connaissance_mot"),
    )


class KnowledgeConflitModel(Base):
    """Conflit bibliographique (S-3 — documentés, jamais résolus arbitrairement)."""

    __tablename__ = "knowledge_conflits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connaissance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_objects.connaissance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_a: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source_b: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    knowledge_object: Mapped[KnowledgeObjectModel] = relationship(back_populates="conflits")


# --- Taxonomie botanique (Phase 2) ---


class BotanicalFamilleModel(Base, TimestampMixin):
    """Famille botanique (ex. Fagaceae, Pinaceae)."""

    __tablename__ = "botanical_familles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom_scientifique: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    nom_commun: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)

    genres: Mapped[list["BotanicalGenreModel"]] = relationship(back_populates="famille")


class BotanicalGenreModel(Base, TimestampMixin):
    """Genre botanique (ex. Quercus, Fagus, Pinus)."""

    __tablename__ = "botanical_genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom_scientifique: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    famille_id: Mapped[int] = mapped_column(
        ForeignKey("botanical_familles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)

    famille: Mapped[BotanicalFamilleModel] = relationship(back_populates="genres")
    essences: Mapped[list["BotanicalEssenceModel"]] = relationship(back_populates="genre")


class BotanicalEssenceModel(Base, TimestampMixin):
    """Essence forestière — espèce botanique (ex. Quercus petraea, chêne sessile).

    Source : BD Forêt IGN, GBIF, BDNFF (Base de Données Nomenclaturale de la Flore de France).
    Chaque essence est liée à des KnowledgeObjects (autécologie, seuils, modèles).
    """

    __tablename__ = "botanical_essences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom_scientifique: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True, index=True
    )
    nom_vernaculaire: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("botanical_genres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Classification forestière
    categorie_forestiere: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # « feuillu », « conifère », « essence_principale », « essence_accompagnement », « pionnière »

    # Caractéristiques botaniques
    type_biologique: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Ex. « Phanérophyte », « Chaméphyte »

    # Répartition géographique
    aire_repartition: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Ex. « Europe tempérée, France métropolitaine »

    # Sources
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    gbif_taxon_key: Mapped[int | None] = mapped_column(nullable=True, index=True)

    # Métadonnées JSONB (flexibilité pour attributs additionnels)
    attributs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))

    genre: Mapped[BotanicalGenreModel] = relationship(back_populates="essences")

    __table_args__ = (
        Index("ix_be_categorie_nom", "categorie_forestiere", "nom_vernaculaire"),
    )


# --- Écosystèmes (Phase 4) ---


class EcosystemHabitatModel(Base, TimestampMixin):
    """Habitat écologique — Natura 2000 (EUR28) / Cahiers d'habitats.

    Source : EUR28 (European Union Interpretation Manual),
    Cahiers d'habitats (MNHN, 1997-2002).
    """

    __tablename__ = "ecosystem_habitats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code_eur28: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    nom_habitat: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    categorie: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Ex. « Forêts », « Pelouses », « Landes », « Tourbières »

    # Intérêt de conservation
    interet_patrimonial: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # « prioritaire », « communautaire », « national »

    # Sources
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)

    # Métadonnées JSONB
    attributs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))


class EcosystemStationModel(Base, TimestampMixin):
    """Type de station forestière — INRAE/ONF.

    Source : Catalogues des types de stations (INRAE, ONF, par région forestière).
    """

    __tablename__ = "ecosystem_stations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code_station: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    nom_station: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Localisation
    region_forestiere: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    departements: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    # Caractéristiques écologiques
    altitude_min: Mapped[int | None] = mapped_column(nullable=True)
    altitude_max: Mapped[int | None] = mapped_column(nullable=True)
    ph_typique: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    rum_typique: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    # Essences adaptées (JSONB — liste de noms scientifiques)
    essences_adaptees: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    essences_potentielles: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    # Sources
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)

    # Métadonnées JSONB
    attributs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))


class EcosystemGroupeEcologiqueModel(Base, TimestampMixin):
    """Groupe écologique — bio-indicateurs (ECOPHYTO, INRAE).

    Source : ECOPHYTO (base de bio-indication floristique, INRAE),
    Dupouey et al. (2011).
    """

    __tablename__ = "ecosystem_groupes_ecologiques"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom_groupe: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Indicateur écologique
    indicateur: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Ex. « pH », « humidité », « trophie », « climat »

    # Valeurs indicatrices (JSONB — structure flexible)
    valeurs_indicatrices: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    # Espèces caractéristiques (JSONB — liste de noms scientifiques)
    especes_caracteristiques: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    # Sources
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
