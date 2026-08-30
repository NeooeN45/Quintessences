"""Portes de qualification d'une source avant requête, fetch ou promotion.

Le registre SCI-001 porte l'identité juridique. Ce module porte les preuves
opérationnelles qui ne doivent pas être déduites d'un simple nom de source.
Les profils sont fournis par l'opérateur ou par un import de fiche ; aucune
valeur par défaut n'autorise un téléchargement ou un entraînement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class QualificationTarget(StrEnum):
    """Niveau d'usage demandé pour une source."""

    QUERY = "QUERY"
    FETCH = "FETCH"
    PROMOTION = "PROMOTION"


@dataclass(frozen=True, slots=True)
class SourceQualificationProfile:
    """Preuves attachées à une distribution précise d'une source."""

    source_id: str
    distribution: str | None = None
    version: str | None = None
    format: str | None = None
    schema: str | None = None
    crs: str | None = None
    spatial: bool = False
    licence_evidence: str | None = None
    access_evidence: str | None = None
    quality_evidence: str | None = None
    quota_policy: str | None = None
    provenance_policy: str | None = None
    operator_fetch_approval: str | None = None
    promotion_evidence: str | None = None
    expert_review: str | None = None
    train_eval_split: str | None = None

    def missing(self, target: QualificationTarget) -> tuple[str, ...]:
        """Retourne les preuves manquantes pour le niveau demandé."""

        required = [
            "distribution",
            "version",
            "format",
            "schema",
            "licence_evidence",
            "access_evidence",
            "quality_evidence",
            "provenance_policy",
        ]
        if self.spatial:
            required.append("crs")
        if target in {QualificationTarget.FETCH, QualificationTarget.PROMOTION}:
            required.extend(("quota_policy", "operator_fetch_approval"))
        if target is QualificationTarget.PROMOTION:
            required.extend(("promotion_evidence", "expert_review", "train_eval_split"))
        return tuple(field for field in required if not getattr(self, field))

    def ready(self, target: QualificationTarget) -> bool:
        """Indique si toutes les preuves requises sont présentes."""

        return not self.missing(target)


def qualification_report(
    profile: SourceQualificationProfile,
) -> dict[str, object]:
    """Produit un rapport JSON-friendly sans modifier le registre."""

    return {
        "source_id": profile.source_id,
        "ready_query": profile.ready(QualificationTarget.QUERY),
        "ready_fetch": profile.ready(QualificationTarget.FETCH),
        "ready_promotion": profile.ready(QualificationTarget.PROMOTION),
        "missing_query": list(profile.missing(QualificationTarget.QUERY)),
        "missing_fetch": list(profile.missing(QualificationTarget.FETCH)),
        "missing_promotion": list(profile.missing(QualificationTarget.PROMOTION)),
    }


__all__ = [
    "QualificationTarget",
    "SourceQualificationProfile",
    "qualification_report",
]
