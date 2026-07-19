"""Modèles forestiers spécialisés — RFC-0016 (schéma forestier spécialisé).

Implémente les tranches verticales suivantes des dix entités du §4 du RFC :

- tranche 1/10 : `AutecologyProfile`, `SiteIndexModel`, `FertilityClass`
  — les trois entités qui portent la règle non négociable :

      Une `FertilityClass` sans `species_entity_id`, `site_index_model_id`,
      âge de référence et région de calibration est un bug de sécurité
      scientifique, pas une simplification acceptable.

- tranche 2/10 : `StationType`, `StationObservation` — diagnostic
  stationnel (étape 2 de la chaîne de décision, RFC-0016 §3.3).

Les cinq entités restantes du §4 (`SilviculturalSystem`/
`SilviculturalRule`/`Intervention`, `ProvenanceMaterial`,
`DiagnosticProtocol`/`HealthRisk`, `EvidenceStatement`/`ConflictRecord`)
restent à implémenter dans une tranche ultérieure.

Convention reprise du Botanical Engine (`_get_or_create_taxon`) : un taxon
est une resource de type `entity` (`entity_subtype="taxon"`), jamais un
identifiant nu (`cd_nom`/`gbif_taxon_key`) stocké directement — ces
identifiants externes passent par `entity_alias`. `species_entity_id`
référence donc systématiquement `entity.id`, jamais un code TAXREF brut.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import EvidenceLevel, LifecycleStatus


@register_type("autecology_profile")
class AutecologyProfileModel(Base, TimestampMixin):
    """Observation autécologique sourcée pour un taxon — une variable à la fois.

    RFC-0016 §4 : jamais une « note globale » par essence — chaque valeur
    (pH optimal, tolérance sécheresse, etc.) est sa propre ligne, avec sa
    propre source et sa propre incertitude.
    """

    __tablename__ = "autecology_profile"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    species_entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    variable: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    life_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    season: Mapped[str | None] = mapped_column(String(50), nullable=True)
    territory_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    method: Mapped[str | None] = mapped_column(Text, nullable=True)
    uncertainty: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        Enum(EvidenceLevel, name="evidence_level"), nullable=False
    )
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False,
        default=LifecycleStatus.draft,
    )

    __table_args__ = (
        CheckConstraint(
            "value_numeric IS NOT NULL OR value_text IS NOT NULL",
            name="ck_autecology_profile_value_present",
        ),
    )


@register_type("site_index_model")
class SiteIndexModelModel(Base, TimestampMixin):
    """Modèle de fertilité (équation/table) pour une essence.

    RFC-0016 §4 : `FertilityClass` doit toujours pouvoir remonter à ce
    modèle (méthode, âge de référence, convention d'âge, région de
    calibration) — sans quoi une « classe 1 » d'un guide n'est pas
    comparable à une « classe 1 » d'un autre (exemple documenté : mémento
    ONF pin d'Alep, classe 1 = hauteur dominante > 14 m à 50 ans — une
    convention parmi d'autres, jamais universelle).
    """

    __tablename__ = "site_index_model"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    species_entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    method: Mapped[str] = mapped_column(String(200), nullable=False)
    reference_age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    age_convention: Mapped[str] = mapped_column(String(200), nullable=False)
    calibration_region: Mapped[str] = mapped_column(String(200), nullable=False)
    valid_age_min_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_age_max_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False,
        default=LifecycleStatus.draft,
    )

    __table_args__ = (
        CheckConstraint(
            "valid_age_min_years IS NULL OR valid_age_max_years IS NULL "
            "OR valid_age_min_years <= valid_age_max_years",
            name="ck_site_index_model_valid_age_range",
        ),
    )


@register_type("fertility_class")
class FertilityClassModel(Base, TimestampMixin):
    """Classe de fertilité contextualisée — jamais un entier nu.

    Règle non négociable (RFC-0016 §3.1) : `species_entity_id`,
    `site_index_model_id`, `reference_age_years`, `calibration_region` et
    `source_id` sont tous obligatoires (`nullable=False`). L'absence de
    l'un de ces champs est un bug de sécurité scientifique, pas une
    simplification acceptable.
    """

    __tablename__ = "fertility_class"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    species_entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    site_index_model_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("site_index_model.id"), nullable=False, index=True
    )
    class_label: Mapped[str] = mapped_column(String(100), nullable=False)
    dominant_height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    lower_bound_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_region: Mapped[str] = mapped_column(String(200), nullable=False)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False,
        default=LifecycleStatus.draft,
    )

    __table_args__ = (
        CheckConstraint(
            "lower_bound_m IS NULL OR upper_bound_m IS NULL OR lower_bound_m <= upper_bound_m",
            name="ck_fertility_class_bounds_order",
        ),
    )


@register_type("station_type")
class StationTypeModel(Base, TimestampMixin):
    """Unité conceptuelle de station issue d'un guide — pas une observation terrain.

    RFC-0016 §4 : porte le guide, sa version et la zone de validité. Une
    `StationObservation` détermine, via la clé de ce guide, quel
    `StationType` s'applique à une parcelle réelle — jamais l'inverse.
    """

    __tablename__ = "station_type"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    guide: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    guide_version: Mapped[str] = mapped_column(String(100), nullable=False)
    validity_zone_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Zone de validité du guide en texte libre (pas de géométrie en tranche 2)",
    )
    ser_greco_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    topography_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    substrate_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hydromorphy_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicator_flora_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False,
        default=LifecycleStatus.draft,
    )


@register_type("station_observation")
class StationObservationModel(Base, TimestampMixin):
    """Ce qui est réellement observé sur une parcelle — jamais confondu avec `StationType`.

    RFC-0016 §4 : conserve le chemin suivi dans la clé du guide
    (`key_path_followed`) et l'incertitude de détermination — une
    observation qui ne résout aucun `StationType` avec certitude doit le
    dire explicitement (`station_type_id` nullable, `determination_uncertainty`
    obligatoire dans ce cas), jamais forcer un rattachement arbitraire.
    """

    __tablename__ = "station_observation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    plot_reference: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    station_type_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("station_type.id"), nullable=True, index=True
    )
    key_path_followed: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Réponses saisies et embranchement obtenu dans la clé du guide"
    )
    topography_observed: Mapped[str | None] = mapped_column(Text, nullable=True)
    substrate_observed: Mapped[str | None] = mapped_column(Text, nullable=True)
    hydromorphy_observed: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicator_flora_observed: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_water_capacity_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    available_water_capacity_method: Mapped[str | None] = mapped_column(String(300), nullable=True)
    determination_uncertainty: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False
    )
    status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status"),
        nullable=False,
        default=LifecycleStatus.draft,
    )

    __table_args__ = (
        CheckConstraint(
            "station_type_id IS NOT NULL OR determination_uncertainty IS NOT NULL",
            name="ck_station_observation_uncertainty_when_undetermined",
        ),
    )
