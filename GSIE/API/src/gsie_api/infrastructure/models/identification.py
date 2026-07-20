"""Identification botanique assistée (Pl@ntNet) — RFC-0018, tranche 1/N.

Implémente le modèle de données de traçabilité décrit en RFC-0018 §5.1
et spécifié fonctionnellement par GEO-004 (GEO-ID-01 à GEO-ID-16) :
trois entités séparées, jamais fusionnées avec `AutecologyProfile`
(RFC-0016), car une identification par photo est une inférence par
individu, pas une observation autécologique validée.

- `BotanicalIdentificationRequestModel` — la capture (photos, organes),
  toujours créée localement avant tout appel réseau (offline-first,
  GEO-ID-02).
- `BotanicalIdentificationResultModel` — la réponse brute d'un
  fournisseur d'identification (Pl@ntNet ou équivalent futur),
  jamais modifiée après réception (GEO-ID-12).
- `BotanicalIdentificationDecisionModel` — la décision humaine
  (`SUGGESTION_IA` / `VALIDEE_UTILISATEUR` / `REJETEE`, GEO-ID-10).
  Seule une décision `validee_utilisateur` autorise un connecteur
  externe (hors périmètre de cette tranche) à alimenter un
  `AutecologyProfile` — cette tranche ne fait qu'enregistrer la
  décision, elle n'écrit jamais elle-même dans le schéma forestier
  (GSIE-CON-001 : l'IA assiste, ne décide jamais).

Cette tranche ne contient aucun appel réseau vers Pl@ntNet — elle pose
uniquement le schéma de traçabilité (DEC-000030). Le client Pl@ntNet,
les routes serveur et le retrait effectif des métadonnées EXIF GPS
sont des tranches ultérieures.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import IdentificationDecisionStatus


@register_type("botanical_identification_request")
class BotanicalIdentificationRequestModel(Base, TimestampMixin):
    """Capture terrain — 1 à 5 photos d'un même individu (GEO-ID-01, GEO-ID-02).

    Toujours créée avant tout envoi réseau : `sent_at` reste `NULL` tant
    que la requête est en file d'attente locale (offline-first).
    """

    __tablename__ = "botanical_identification_request"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    requested_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    parcel_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True, index=True
    )
    photos: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False, default=list)
    """Liste de `{"organ": PlantOrgan, "content_hash": str}` — empreinte
    numérique conservée (GEO-ID-12), jamais le fichier source lui-même
    dans cette table (le stockage image relève d'un autre composant)."""

    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    """`NULL` tant que la requête est en file d'attente offline (GEO-ID-14)."""

    # Le nombre de photos (1 à 5, GEO-ID-01) est validé au niveau applicatif
    # (schéma Pydantic de l'engine, tranche ultérieure) plutôt qu'en
    # CheckConstraint SQL : `jsonb_array_length` est spécifique PostgreSQL
    # et n'existe pas sous SQLite, utilisé par la suite de tests unitaires.


@register_type("botanical_identification_result")
class BotanicalIdentificationResultModel(Base, TimestampMixin):
    """Réponse brute d'un fournisseur d'identification (GEO-ID-06, GEO-ID-12).

    Immuable après création : une nouvelle interrogation du même
    fournisseur produit une nouvelle ligne, jamais une mise à jour de
    celle-ci (traçabilité de chaque appel, GSIE-CON-005).
    """

    __tablename__ = "botanical_identification_result"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="plantnet")
    provider_engine_version: Mapped[str] = mapped_column(String(100), nullable=False)
    candidates: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    """Jusqu'à N candidats : `{"scientific_name", "family", "score",
    "gbif_taxon_key", "povo_id"}` — au moins les 3 meilleures hypothèses
    doivent être conservées ici pour respecter GEO-ID-05/GEO-ID-06."""

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Au moins un candidat (GEO-ID-06) est validé au niveau applicatif pour
    # la même raison que ci-dessus (portabilité SQLite/PostgreSQL).


@register_type("botanical_identification_decision")
class BotanicalIdentificationDecisionModel(Base, TimestampMixin):
    """Décision humaine sur un résultat d'identification (GEO-ID-08, GEO-ID-10).

    Principe non négociable (RFC-0018 §4) : `status='suggestion_ia'`
    tant qu'aucune décision explicite n'a été enregistrée. Aucune
    valeur par défaut ne bascule automatiquement vers
    `validee_utilisateur`, quel que soit le score du meilleur candidat.
    """

    __tablename__ = "botanical_identification_decision"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=False, index=True
    )
    status: Mapped[IdentificationDecisionStatus] = mapped_column(
        Enum(IdentificationDecisionStatus, name="identification_decision_status"),
        nullable=False,
        default=IdentificationDecisionStatus.suggestion_ia,
    )
    selected_candidate_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    """Index dans `BotanicalIdentificationResultModel.candidates` du
    candidat confirmé — `NULL` si `status != validee_utilisateur` ou si
    l'espèce a été identifiée manuellement hors des candidats proposés."""

    manual_species_entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    """Renseigné uniquement si le technicien a choisi « Identifier
    manuellement » (GEO-ID-08) plutôt qu'une hypothèse proposée."""

    validated_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resource.id"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(status != 'validee_utilisateur') OR "
            "(validated_by_id IS NOT NULL AND decided_at IS NOT NULL AND "
            "(selected_candidate_index IS NOT NULL OR manual_species_entity_id IS NOT NULL))",
            name="ck_bid_validation_requires_evidence",
        ),
        CheckConstraint(
            "(status != 'rejetee') OR "
            "(validated_by_id IS NOT NULL AND decided_at IS NOT NULL)",
            name="ck_bid_rejection_requires_validator",
        ),
    )
