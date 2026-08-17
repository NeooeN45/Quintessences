"""Réconciliation fail-closed des identités SCI-001 historiques.

Le manifeste Data Registry du 10 août 2026 a persisté quatre identités trop
agrégées. Ce module ne les réécrit jamais automatiquement : une scission peut
changer le producteur, la licence, le canal d'accès et l'identité stable des
ressources. Il fournit uniquement l'audit déterministe préalable à une
migration transactionnelle explicite.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from gsie_api.governance.source_registry import get_source

if TYPE_CHECKING:
    from gsie_api.ingestion.manifest import DatasetManifest


class SourceReconciliationRequiredError(ValueError):
    """Le manifeste référence une identité historique qui exige une décision."""


@dataclass(frozen=True, slots=True)
class LegacySourceReference:
    """Référence d'une entrée de manifeste vers une source SCI-001 dépréciée."""

    slug: str
    version: str
    legacy_source_id: str
    successor_ids: tuple[str, ...]


class DryRunDecision(StrEnum):
    """Décision non mutante produite par le dry-run d'identité."""

    proposed = "PROPOSED"
    unresolved = "UNRESOLVED"
    preserve_lineage = "PRESERVE_LINEAGE"


@dataclass(frozen=True, slots=True)
class AdapterProposal:
    """Correspondance étayée pour les futures fiches, hors migration historique."""

    adapter_key: str
    target_source_id: str
    confidence: str
    scope: str


@dataclass(frozen=True, slots=True)
class MigrationDryRunItem:
    """Résultat d'une ligne historique, sans identifiant ni écriture SQL."""

    legacy_slug: str
    legacy_source_id: str
    candidate_source_ids: tuple[str, ...]
    decision: DryRunDecision
    proposed_source_id: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class MigrationDryRunReport:
    """Rapport sérialisable du dry-run de scission SCI-001."""

    mode: str
    writes: int
    fetch_enabled: bool
    promotion_allowed: bool
    items: tuple[MigrationDryRunItem, ...]
    adapter_proposals: tuple[AdapterProposal, ...]

    def as_dict(self) -> dict[str, object]:
        """Retourne une représentation JSON stable et explicitement non mutante."""

        return {
            "mode": self.mode,
            "writes": self.writes,
            "fetch_enabled": self.fetch_enabled,
            "promotion_allowed": self.promotion_allowed,
            "items": [
                {
                    "legacy_slug": item.legacy_slug,
                    "legacy_source_id": item.legacy_source_id,
                    "candidate_source_ids": list(item.candidate_source_ids),
                    "decision": item.decision.value,
                    "proposed_source_id": item.proposed_source_id,
                    "reason": item.reason,
                }
                for item in self.items
            ],
            "adapter_proposals": [
                {
                    "adapter_key": proposal.adapter_key,
                    "target_source_id": proposal.target_source_id,
                    "confidence": proposal.confidence,
                    "scope": proposal.scope,
                }
                for proposal in self.adapter_proposals
            ],
        }


_ADAPTER_PROPOSALS = (
    AdapterProposal(
        adapter_key="gbif",
        target_source_id="gbif-species-api",
        confidence="high",
        scope="nouvelles métadonnées Species API uniquement ; aucune occurrence historique",
    ),
    AdapterProposal(
        adapter_key="meteofrance",
        target_source_id="meteofrance-meteo-forets",
        confidence="high",
        scope="opération danger_feux_departements uniquement",
    ),
)


def find_legacy_source_references(manifest: DatasetManifest) -> tuple[LegacySourceReference, ...]:
    """Liste les identités agrégées sans modifier le manifeste."""

    references: list[LegacySourceReference] = []
    for entry in manifest.entries:
        source = get_source(entry.source_registry_id)
        if source is not None and source.deprecated:
            references.append(
                LegacySourceReference(
                    slug=entry.slug,
                    version=entry.version,
                    legacy_source_id=entry.source_registry_id,
                    successor_ids=source.successor_ids,
                )
            )
    return tuple(references)


def require_canonical_source_references(manifest: DatasetManifest) -> None:
    """Refuse un futur manifeste contenant une identité historique agrégée."""

    references = find_legacy_source_references(manifest)
    if not references:
        return
    details = "; ".join(
        f"{item.slug}@{item.version}: {item.legacy_source_id} -> "
        f"{', '.join(item.successor_ids)}"
        for item in references
    )
    raise SourceReconciliationRequiredError(
        "Réconciliation SCI-001 obligatoire avant application : " + details
    )


def build_migration_dry_run(
    historical_manifest: DatasetManifest,
    candidate_manifest: DatasetManifest,
) -> MigrationDryRunReport:
    """Compare deux manifestes sans toucher à PostgreSQL, MinIO ou aux fournisseurs.

    Les identités historiques restent ``UNRESOLVED`` lorsqu'une ventilation
    scientifique ne peut pas être prouvée par le contenu existant. SoilGrids
    est marqué ``PRESERVE_LINEAGE`` : son DataAsset DEC-000061 ne doit pas être
    renommé automatiquement vers le candidat WCS.
    """

    candidate_source_ids = tuple(
        sorted({entry.source_registry_id for entry in candidate_manifest.entries})
    )
    candidate_set = set(candidate_source_ids)
    items: list[MigrationDryRunItem] = []
    for reference in find_legacy_source_references(historical_manifest):
        if reference.legacy_source_id == "soilgrids" and "soilgrids-wcs" in candidate_set:
            items.append(
                MigrationDryRunItem(
                    legacy_slug=reference.slug,
                    legacy_source_id=reference.legacy_source_id,
                    candidate_source_ids=reference.successor_ids,
                    decision=DryRunDecision.preserve_lineage,
                    proposed_source_id="soilgrids-wcs",
                    reason=(
                        "DataAsset DEC-000061 conservé sur l'identité historique ; "
                        "aucun renommage automatique vers WCS."
                    ),
                )
            )
            continue
        items.append(
            MigrationDryRunItem(
                legacy_slug=reference.slug,
                legacy_source_id=reference.legacy_source_id,
                candidate_source_ids=reference.successor_ids,
                decision=DryRunDecision.unresolved,
                proposed_source_id=None,
                reason=(
                    "Le contenu persisté est metadata_only sans opération, couche "
                    "ou jeu constitutif : preuve insuffisante pour migrer."
                ),
            )
        )
    return MigrationDryRunReport(
        mode="DRY_RUN_ONLY",
        writes=0,
        fetch_enabled=False,
        promotion_allowed=False,
        items=tuple(items),
        adapter_proposals=_ADAPTER_PROPOSALS,
    )


__all__ = [
    "LegacySourceReference",
    "AdapterProposal",
    "DryRunDecision",
    "MigrationDryRunItem",
    "MigrationDryRunReport",
    "SourceReconciliationRequiredError",
    "build_migration_dry_run",
    "find_legacy_source_references",
    "require_canonical_source_references",
]
