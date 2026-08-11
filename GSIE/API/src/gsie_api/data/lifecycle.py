"""Machine d'état du Registry (RFC-0038 §6.1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

from gsie_api.infrastructure.models.enums import DatasetStatus


class InvalidDatasetTransitionError(ValueError):
    """Transition de statut non prévue par le contrat Registry."""


# Alias de compatibilité pour les premiers consommateurs de la tranche.
InvalidDatasetTransition = InvalidDatasetTransitionError


TRANSITIONS: Mapping[DatasetStatus, frozenset[DatasetStatus]] = {
    DatasetStatus.discovered: frozenset({DatasetStatus.link_checked, DatasetStatus.broken}),
    DatasetStatus.link_checked: frozenset({DatasetStatus.metadata_extracted, DatasetStatus.broken}),
    DatasetStatus.metadata_extracted: frozenset(
        {DatasetStatus.license_analyzed, DatasetStatus.broken}
    ),
    DatasetStatus.license_analyzed: frozenset(
        {
            DatasetStatus.coverage_analyzed,
            DatasetStatus.unknown_license,
            DatasetStatus.license_restricted,
        }
    ),
    DatasetStatus.coverage_analyzed: frozenset(
        {DatasetStatus.schema_analyzed, DatasetStatus.broken}
    ),
    DatasetStatus.schema_analyzed: frozenset(
        {DatasetStatus.security_checked, DatasetStatus.broken}
    ),
    DatasetStatus.security_checked: frozenset({DatasetStatus.validated, DatasetStatus.broken}),
    DatasetStatus.validated: frozenset({DatasetStatus.staging, DatasetStatus.experimental}),
    DatasetStatus.staging: frozenset(
        {DatasetStatus.production, DatasetStatus.experimental, DatasetStatus.broken}
    ),
    DatasetStatus.production: frozenset({DatasetStatus.deprecated, DatasetStatus.unavailable}),
    DatasetStatus.deprecated: frozenset({DatasetStatus.archived}),
    DatasetStatus.broken: frozenset(),
    DatasetStatus.unavailable: frozenset({DatasetStatus.link_checked}),
    DatasetStatus.license_restricted: frozenset({DatasetStatus.license_analyzed}),
    DatasetStatus.unknown_license: frozenset({DatasetStatus.license_analyzed}),
    DatasetStatus.archived: frozenset(),
    DatasetStatus.experimental: frozenset({DatasetStatus.staging, DatasetStatus.archived}),
}


def _coerce_status(value: DatasetStatus | str) -> DatasetStatus:
    try:
        return value if isinstance(value, DatasetStatus) else DatasetStatus(value)
    except (TypeError, ValueError) as exc:
        raise InvalidDatasetTransition(f"Statut Registry inconnu : {value!r}") from exc


def can_transition(current: DatasetStatus | str, target: DatasetStatus | str) -> bool:
    """Indique si la transition explicite est autorisée."""
    try:
        current_status = _coerce_status(current)
        target_status = _coerce_status(target)
    except InvalidDatasetTransition:
        return False
    return target_status in TRANSITIONS[current_status]


def transition_status(current: DatasetStatus | str, target: DatasetStatus | str) -> DatasetStatus:
    """Valide une transition et retourne le statut cible normalisé."""
    current_status = _coerce_status(current)
    target_status = _coerce_status(target)
    if target_status not in TRANSITIONS[current_status]:
        raise InvalidDatasetTransition(
            f"Transition Registry interdite : {current_status.value} -> {target_status.value}"
        )
    return target_status
