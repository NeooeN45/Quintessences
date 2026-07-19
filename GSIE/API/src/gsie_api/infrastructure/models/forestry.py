"""Modèles forestiers spécialisés — RFC-0016 (schéma forestier spécialisé).

Implémente une première tranche verticale des dix entités du §4 du RFC :
`AutecologyProfile`, `SiteIndexModel`, `FertilityClass` — les trois
entités qui portent la règle non négociable :

    Une `FertilityClass` sans `species_entity_id`, `site_index_model_id`,
    âge de référence et région de calibration est un bug de sécurité
    scientifique, pas une simplification acceptable.

Les sept autres entités du §4 (`StationType`/`StationObservation`,
`SilviculturalSystem`/`SilviculturalRule`/`Intervention`,
`ProvenanceMaterial`, `DiagnosticProtocol`/`HealthRisk`,
`EvidenceStatement`/`ConflictRecord`) restent à implémenter dans une
tranche ultérieure.

Convention reprise du Botanical Engine (`_get_or_create_taxon`) : un taxon
est une resource de type `entity` (`entity_subtype="taxon"`), jamais un
identifiant nu (`cd_nom`/`gbif_taxon_key`) stocké directement — ces
identifiants externes passent par `entity_alias`. `species_entity_id`
référence donc systématiquement `entity.id`, jamais un code TAXREF brut.
"""

from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, Float, ForeignKey, Integer, String, Text
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
