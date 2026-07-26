"""Diagnostic stationnel persisté — type de resource `diagnostic`.

Ce type est créé pour la persistance du Diagnostic Engine (chantier P0
« Persistance des diagnostics », `PROJECT_MEMORY.md`). Il rend un
`diagnostic_id` résolvable, ce qu'exige `RecommendationRequest`
(`RECOMMENDATION_ENGINE.md` §5) et que le moteur, sans effet de bord, ne
permettait pas.

**Pourquoi un type neuf plutôt qu'un type existant.** Le métamodèle v6.2
contient déjà `inference`, `recommendation` et `diagnostic_protocol`.
Aucun des trois ne désigne cet objet :

- `inference` est la prédiction d'un **modèle statistique**
  (`model_version_id`, `feature_set_id`) ;
- `recommendation` est une recommandation générique portée par un acteur
  (`recommended_by`, `recommendation_text`) ;
- `diagnostic_protocol` est un **protocole** sanitaire (RFC-0016), c'est-à-dire
  une méthode, pas un résultat.

Ranger un diagnostic dans `inference` rendrait indistinguables en base une
conclusion tracée par règles explicites et une prédiction opaque : le
lecteur ne pourrait plus savoir laquelle il conteste, ce que `GSIE-CON-004`
interdit.

**Où vit la vérité.** `contenu` porte le `Diagnostic` sérialisé intégral et
constitue la seule source de relecture. Les colonnes scalaires en sont des
projections destinées aux index et aux requêtes ; elles ne sont jamais lues
pour reconstruire un diagnostic, ce qui interdit toute divergence
observable entre les deux.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models.base import Base, TimestampMixin, register_type
from gsie_api.infrastructure.models.enums import (
    DiagnosticGlobalState,
    DiagnosticType,
    DiagnosticValidationStatus,
    EvidenceLevel,
)


@register_type("diagnostic")
class DiagnosticModel(Base, TimestampMixin):
    """Diagnostic stationnel produit par le Diagnostic Engine.

    `station_id` et `requete_origine` ne portent pas de clé étrangère vers
    `resource` : une requête de diagnostic est identifiée par l'appelant et
    n'a pas de ligne `resource`, et une station peut être décrite par le
    contexte de la requête sans être encore enregistrée. Une FK
    transformerait ces deux cas légitimes en erreur serveur sur un
    diagnostic pourtant valide. Les deux colonnes restent indexées, car
    « tous les diagnostics de cette station » est la requête de lecture
    attendue côté Recommendation.
    """

    __tablename__ = "diagnostic"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        primary_key=True,
    )
    requete_origine: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    type_diagnostic: Mapped[DiagnosticType] = mapped_column(
        Enum(
            DiagnosticType,
            name="diagnostic_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    etat_global: Mapped[DiagnosticGlobalState] = mapped_column(
        Enum(
            DiagnosticGlobalState,
            name="diagnostic_global_state",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    statut_validation: Mapped[DiagnosticValidationStatus] = mapped_column(
        Enum(
            DiagnosticValidationStatus,
            name="diagnostic_validation_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    confiance: Mapped[float] = mapped_column(Float, nullable=False)
    # `values_callable` obligatoire : les membres d'EvidenceLevel ont un nom
    # en minuscule (a, b, …) et une valeur en majuscule (A, B, …), et le type
    # PostgreSQL `evidence_level` créé en 0002 porte les majuscules.
    evidence_level_plancher: Mapped[EvidenceLevel] = mapped_column(
        Enum(
            EvidenceLevel,
            name="evidence_level",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    date_diagnostic: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    contenu: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Diagnostic sérialisé intégral — seule source de relecture",
    )

    __table_args__ = (Index("ix_diagnostic_station_date", "station_id", "date_diagnostic"),)
