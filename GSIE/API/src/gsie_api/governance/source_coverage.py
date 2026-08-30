"""Matrice exécutable de couverture des sources GSIE et Forge.

Le registre juridique reste la source de vérité pour les droits. Cette matrice
ajoute uniquement l'état opérationnel observé dans le code : adapter de
requête, handoff Forge, métadonnées seules, fouille éphémère, verrou
partenaire, blocage ou absence de branchement.

Elle est volontairement exhaustive : l'ajout d'une source dans
``source_registry.py`` impose de déclarer sa couverture ici avant qu'un job ou
un moteur puisse la considérer comme disponible. Une entrée ``ADAPTER_QUERY``
ne signifie pas qu'une copie ou une indexation est autorisée.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from gsie_api.data.adapters import AdapterCapability, AdapterPluginRegistry
from gsie_api.data.bootstrap import build_adapter_registry
from gsie_api.governance.source_registry import (
    SCIENTIFIC_SOURCES,
    IngestionMode,
    ScientificSourceEntry,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class SourceOperationalStatus(StrEnum):
    """État d'exploitation déclaré pour une source scientifique."""

    ADAPTER_QUERY = "ADAPTER_QUERY"
    FORGE_HANDOFF = "FORGE_HANDOFF"
    METADATA_ONLY = "METADATA_ONLY"
    EPHEMERAL_TDM = "EPHEMERAL_TDM"
    PARTNER_GATE = "PARTNER_GATE"
    BLOCKED = "BLOCKED"
    UNWIRED_OPEN_COPY = "UNWIRED_OPEN_COPY"
    HISTORICAL = "HISTORICAL"


@dataclass(frozen=True, slots=True)
class SourceCoverage:
    """Déclaration d'un branchement sans promesse de qualification métier."""

    source_id: str
    status: SourceOperationalStatus
    integration: str
    adapter_key: str | None = None
    required_capability: AdapterCapability | None = None
    canonical_surface: str | None = None
    blocking_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SourceCoverageAudit:
    """Résultat stable de l'audit de couverture de toutes les sources."""

    entries: tuple[SourceCoverage, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Indique si la matrice est complète et cohérente avec les registres."""

        return not self.errors

    @property
    def counts(self) -> dict[str, int]:
        """Retourne des compteurs JSON-friendly dans un ordre déterministe."""

        return dict(sorted(Counter(item.status.value for item in self.entries).items()))


def _coverage(
    source_id: str,
    status: SourceOperationalStatus,
    integration: str,
    *,
    adapter_key: str | None = None,
    required_capability: AdapterCapability | None = None,
    canonical_surface: str | None = None,
    blocking_reason: str | None = None,
) -> SourceCoverage:
    return SourceCoverage(
        source_id=source_id,
        status=status,
        integration=integration,
        adapter_key=adapter_key,
        required_capability=required_capability,
        canonical_surface=canonical_surface,
        blocking_reason=blocking_reason,
    )


# Cette table est la porte de complétude : aucune source ne peut être oubliée
# silencieusement lors d'une extension de SCIENTIFIC_SOURCES.
SOURCE_COVERAGE: tuple[SourceCoverage, ...] = (
    _coverage(
        "meteofrance-portail-api", SourceOperationalStatus.HISTORICAL, "identité agrégée obsolète"
    ),
    _coverage(
        "meteofrance-meteo-forets",
        SourceOperationalStatus.ADAPTER_QUERY,
        "Data Registry adapter MeteoFranceAdapter",
        adapter_key="meteofrance",
        required_capability=AdapterCapability.QUERY,
        canonical_surface="Météo des forêts v1",
    ),
    _coverage(
        "meteofrance-safran", SourceOperationalStatus.METADATA_ONLY, "catalogue et lien seulement"
    ),
    _coverage(
        "meteofrance-arpege-arome",
        SourceOperationalStatus.METADATA_ONLY,
        "catalogue et lien seulement ; client scientifique hors Data Registry",
    ),
    _coverage(
        "meteofrance-observations-sol",
        SourceOperationalStatus.METADATA_ONLY,
        "catalogue et lien seulement ; grain et distribution à qualifier",
    ),
    _coverage("gbif", SourceOperationalStatus.HISTORICAL, "identité agrégée obsolète"),
    _coverage(
        "gbif-species-api",
        SourceOperationalStatus.ADAPTER_QUERY,
        "Data Registry adapter GBIFAdapter",
        adapter_key="gbif",
        required_capability=AdapterCapability.QUERY,
        canonical_surface="Species API / résolution taxonomique",
    ),
    _coverage(
        "gbif-occurrence-datasets",
        SourceOperationalStatus.METADATA_ONLY,
        "catalogue et DOI par dataset ; licences constitutives à filtrer",
    ),
    _coverage(
        "taxref-via-gbif",
        SourceOperationalStatus.ADAPTER_QUERY,
        "Data Registry adapter TaxrefAdapter via miroir GBIF",
        adapter_key="taxref",
        required_capability=AdapterCapability.QUERY,
        canonical_surface="jeu TAXREF miroir GBIF",
    ),
    _coverage("soilgrids", SourceOperationalStatus.HISTORICAL, "identité agrégée obsolète"),
    _coverage(
        "soilgrids-wcs",
        SourceOperationalStatus.ADAPTER_QUERY,
        "Data Registry adapter SoilGridsAdapter via WCS ISRIC",
        adapter_key="soilgrids",
        required_capability=AdapterCapability.QUERY,
        canonical_surface="WCS 2.0.1 maps.isric.org/mapserv",
        blocking_reason="FETCH reste fermé par le registre de qualification opérateur",
    ),
    _coverage(
        "soilgrids-rest-beta",
        SourceOperationalStatus.BLOCKED,
        "aucune ingestion",
        canonical_surface="REST bêta suspendu",
        blocking_reason="source DO_NOT_INGEST ; aucun adapter de production ne doit la cibler",
    ),
    _coverage(
        "ign-apicarto-geopf", SourceOperationalStatus.HISTORICAL, "identité agrégée obsolète"
    ),
    _coverage(
        "ign-apicarto-cadastre",
        SourceOperationalStatus.ADAPTER_QUERY,
        "Data Registry adapter IGNAdapter",
        adapter_key="ign",
        required_capability=AdapterCapability.QUERY,
        canonical_surface="API Carto cadastre",
    ),
    _coverage(
        "ign-apicarto-limites-administratives",
        SourceOperationalStatus.METADATA_ONLY,
        "adapter IGN actuel non spécialisé sur les limites administratives",
    ),
    _coverage(
        "ign-apicarto-wfs-geoplateforme",
        SourceOperationalStatus.METADATA_ONLY,
        "catalogue et lien seulement ; aucune couche arbitraire",
    ),
    _coverage(
        "ifn-donnees-brutes",
        SourceOperationalStatus.FORGE_HANDOFF,
        "connecteur Forge IFN + gsie_acquisition_handoff.v1",
        canonical_surface="archive brute IFN vérifiée par taille et SHA-256",
    ),
    _coverage(
        "indigenat-bellifa-2026",
        SourceOperationalStatus.ADAPTER_QUERY,
        "Data Registry adapter IndigenatBellifaAdapter sur fichier versionné",
        adapter_key="indigenat-bellifa",
        required_capability=AdapterCapability.QUERY,
        canonical_surface="jeu Recherche Data Gouv / DOI",
    ),
    _coverage(
        "climessences",
        SourceOperationalStatus.METADATA_ONLY,
        "lien et citation seulement",
        blocking_reason="autorisation écrite obligatoire avant copie ou indexation",
    ),
    _coverage(
        "bioclimsol",
        SourceOperationalStatus.PARTNER_GATE,
        "intégration partenaire sous licence",
        blocking_reason="aucun scraping ni clone sans accord CNPF",
    ),
    _coverage(
        "cnpf-itineraires-guides",
        SourceOperationalStatus.METADATA_ONLY,
        "lien et citation seulement",
        blocking_reason="réutilisation et redistribution à autoriser par le CNPF",
    ),
    _coverage(
        "hal-depot-auteur",
        SourceOperationalStatus.EPHEMERAL_TDM,
        "Forge documents HAL : extraction de faits atomiques puis destruction",
        canonical_surface="dépôt auteur HAL",
        blocking_reason="aucune redistribution du PDF ou du texte intégral",
    ),
    _coverage(
        "onf-guides-sylviculture",
        SourceOperationalStatus.METADATA_ONLY,
        "collection et citation seulement",
        blocking_reason="régime de réutilisation à qualifier document par document",
    ),
)


def audit_source_coverage(
    *,
    adapter_registry: AdapterPluginRegistry | None = None,
    source_entries: Mapping[str, ScientificSourceEntry] | None = None,
) -> SourceCoverageAudit:
    """Vérifie la complétude de la matrice et les capacités réellement montées.

    Le contrôle ne réalise aucun appel réseau et n'instancie aucun adapter.
    Il est donc utilisable dans la CI, avant toute campagne de santé ou de
    FETCH. Les adapters existants mais non reliés à une source sont signalés,
    ce qui détecte notamment le chemin SoilGrids REST interdit.
    """

    entries_by_id = SCIENTIFIC_SOURCES if source_entries is None else source_entries
    adapters = adapter_registry or build_adapter_registry()
    errors: list[str] = []
    coverage_by_id: dict[str, SourceCoverage] = {}
    descriptor_by_key = {descriptor.key: descriptor for descriptor in adapters.descriptors()}

    for item in SOURCE_COVERAGE:
        if item.source_id in coverage_by_id:
            errors.append(f"SOURCE_COVERAGE_DUPLICATE:{item.source_id}")
        coverage_by_id[item.source_id] = item

    source_ids = set(entries_by_id)
    coverage_ids = set(coverage_by_id)
    for source_id in sorted(source_ids - coverage_ids):
        errors.append(f"SOURCE_COVERAGE_MISSING:{source_id}")
    for source_id in sorted(coverage_ids - source_ids):
        errors.append(f"SOURCE_COVERAGE_UNKNOWN:{source_id}")

    bound_adapter_keys: set[str] = set()
    for item in SOURCE_COVERAGE:
        entry = entries_by_id.get(item.source_id)
        if entry is None:
            continue
        if entry.deprecated and item.status is not SourceOperationalStatus.HISTORICAL:
            errors.append(f"SOURCE_DEPRECATED_NOT_HISTORICAL:{item.source_id}")
        if (
            item.status is SourceOperationalStatus.UNWIRED_OPEN_COPY
            and entry.mode_ingestion is not IngestionMode.open_copy
        ):
            errors.append(f"SOURCE_UNWIRED_MODE_MISMATCH:{item.source_id}")
        if (
            item.status is SourceOperationalStatus.FORGE_HANDOFF
            and item.source_id != "ifn-donnees-brutes"
        ):
            errors.append(f"SOURCE_FORGE_HANDOFF_UNJUSTIFIED:{item.source_id}")
        if item.status is SourceOperationalStatus.ADAPTER_QUERY:
            if item.adapter_key is None or item.required_capability is None:
                errors.append(f"SOURCE_ADAPTER_BINDING_INCOMPLETE:{item.source_id}")
                continue
            bound_adapter_keys.add(item.adapter_key)
            descriptor = descriptor_by_key.get(item.adapter_key)
            if descriptor is None:
                errors.append(f"SOURCE_ADAPTER_MISSING:{item.source_id}:{item.adapter_key}")
            elif item.required_capability not in descriptor.capabilities:
                errors.append(
                    f"SOURCE_ADAPTER_CAPABILITY_MISSING:{item.source_id}:{item.adapter_key}:{item.required_capability.value}"
                )
            if entry.mode_ingestion not in {
                IngestionMode.metadata_link,
                IngestionMode.open_copy,
            }:
                errors.append(f"SOURCE_ADAPTER_QUERY_REQUIRES_METADATA_OR_OPEN_COPY:{item.source_id}")

    for descriptor in adapters.descriptors():
        if descriptor.key not in bound_adapter_keys:
            errors.append(f"ADAPTER_WITHOUT_SOURCE_BINDING:{descriptor.key}")

    return SourceCoverageAudit(
        entries=tuple(sorted(SOURCE_COVERAGE, key=lambda item: item.source_id)),
        errors=tuple(sorted(set(errors))),
    )


__all__ = [
    "SOURCE_COVERAGE",
    "SourceCoverage",
    "SourceCoverageAudit",
    "SourceOperationalStatus",
    "audit_source_coverage",
]
