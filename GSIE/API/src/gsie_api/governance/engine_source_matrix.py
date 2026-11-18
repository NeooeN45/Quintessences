"""Matrice exécutable des dépendances sources des 14 moteurs GSIE.

Cette matrice rend explicite la frontière entre une source interrogée par un
adapter Data Registry, une acquisition livrée par Forge puis vérifiée par GSIE
et une donnée transverse consommée indirectement après qualification.

Les intitulés de recherche non encore présents dans le registre canonique
restent documentés comme candidats. Ils ne constituent jamais une autorisation
d'egress ou d'ingestion.
"""

# ruff: noqa: TC003

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from gsie_api.benchmark.adapters import engine_contract_catalog
from gsie_api.governance.source_coverage import (
    SOURCE_COVERAGE,
    SourceCoverage,
    SourceOperationalStatus,
)
from gsie_api.governance.source_registry import SCIENTIFIC_SOURCES, ScientificSourceEntry


class EngineSourceMode(StrEnum):
    """Mode de dépendance d'un moteur vis-à-vis des données."""

    INDIRECT_REGISTRY = "INDIRECT_REGISTRY"
    ADAPTER_QUERY = "ADAPTER_QUERY"
    FORGE_HANDOFF = "FORGE_HANDOFF"


@dataclass(frozen=True, slots=True)
class EngineSourceBinding:
    """Dépendances déclarées d'un moteur.

    ``candidate_sources`` est purement documentaire. Seuls les identifiants
    de ``source_ids`` sont vérifiés contre le registre canonique.
    """

    engine_id: str
    mode: EngineSourceMode
    source_ids: tuple[str, ...] = ()
    purpose: str = ""
    candidate_sources: tuple[str, ...] = ()
    pending_source_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EngineSourceMatrixAudit:
    """Résultat déterministe du contrôle moteur vers source."""

    bindings: tuple[EngineSourceBinding, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Indique si chaque dépendance déclarée est cohérente et autorisée."""

        return not self.errors

    @property
    def counts(self) -> dict[str, int]:
        """Retourne les compteurs de modes dans un ordre stable."""

        return dict(sorted(Counter(item.mode.value for item in self.bindings).items()))


# Les contrats sont définis une seule fois dans GSIE-Bench. Cette matrice ne
# duplique donc pas la liste des 14 moteurs : elle la contrôle.
ENGINE_SOURCE_MATRIX: tuple[EngineSourceBinding, ...] = (
    EngineSourceBinding(
        "evidence",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Qualification des preuves et des références du pipeline.",
    ),
    EngineSourceBinding(
        "knowledge",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Consommation de connaissances déjà qualifiées par Evidence.",
    ),
    EngineSourceBinding(
        "gis",
        EngineSourceMode.ADAPTER_QUERY,
        ("ign-apicarto-cadastre",),
        "Parcelle et caractéristiques géographiques via l'adapter IGN.",
        ("BD Forêt v2", "LiDAR HD", "BD Ortho", "Sentinel-2"),
        ("ign-apicarto-limites-administratives", "ign-apicarto-wfs-geoplateforme"),
    ),
    EngineSourceBinding(
        "climate",
        EngineSourceMode.ADAPTER_QUERY,
        ("meteofrance-meteo-forets",),
        "Danger de feux par département via Météo des forêts.",
        ("SAFRAN", "ARPEGE/AROME", "Observations du sol"),
        (
            "meteofrance-safran",
            "meteofrance-arpege-arome",
            "meteofrance-observations-sol",
        ),
    ),
    EngineSourceBinding(
        "pedology",
        EngineSourceMode.ADAPTER_QUERY,
        ("soilgrids-wcs",),
        "Propriétés pédologiques ponctuelles via WCS 2.0.1.",
        ("BDAT", "InfoTerre BRGM", "RMQS", "GIS Sol/IGCS"),
    ),
    EngineSourceBinding(
        "botanical",
        EngineSourceMode.ADAPTER_QUERY,
        ("gbif-species-api", "taxref-via-gbif", "indigenat-bellifa-2026"),
        "Résolution taxonomique et indigénat versionné.",
        ("OpenObs", "Faune-France", "Tela Botanica"),
        ("gbif-occurrence-datasets",),
    ),
    EngineSourceBinding(
        "correlation",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Corrélation de variables déjà normalisées et qualifiées.",
    ),
    EngineSourceBinding(
        "forest_dynamics",
        EngineSourceMode.FORGE_HANDOFF,
        ("ifn-donnees-brutes",),
        "Calibration dendrométrique via handoff Forge vérifié par manifeste.",
        ("BD Forêt v2", "LiDAR HD", "RENECOFOR"),
    ),
    EngineSourceBinding(
        "reasoning",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Raisonnement sur les faits et chaînes de preuve qualifiés.",
    ),
    EngineSourceBinding(
        "diagnostic",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Diagnostic sur les données domaine hydratées et leurs preuves.",
        candidate_sources=("BD Forêt v2", "BDAT", "DSF", "INPN"),
    ),
    EngineSourceBinding(
        "recommendation",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Recommandation sur un diagnostic validé, jamais sur un fournisseur direct.",
    ),
    EngineSourceBinding(
        "validation",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Validation des résultats, sources et niveaux de preuve.",
    ),
    EngineSourceBinding(
        "simulation",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Simulation à partir d'un scénario et de variables qualifiées.",
        candidate_sources=("DRIAS", "LiDAR HD", "BD Ortho", "BDIFF"),
    ),
    EngineSourceBinding(
        "learning",
        EngineSourceMode.INDIRECT_REGISTRY,
        purpose="Apprentissage uniquement à partir de jeux explicitement promus.",
        candidate_sources=("GSIE-Bench Open/Silver",),
    ),
)


def audit_engine_source_matrix(
    *,
    bindings: Iterable[EngineSourceBinding] | None = None,
    source_entries: Mapping[str, ScientificSourceEntry] | None = None,
    coverage_entries: Iterable[SourceCoverage] = SOURCE_COVERAGE,
) -> EngineSourceMatrixAudit:
    """Vérifie les 14 contrats moteur et leurs dépendances sources.

    Le contrôle est sans réseau, sans instanciation d'adapter et sans accès à
    la base. Il interdit notamment qu'un moteur déclare directement une source
    historique, bloquée ou non couverte par le mécanisme prévu.
    """

    entries = tuple(ENGINE_SOURCE_MATRIX if bindings is None else bindings)
    source_map = SCIENTIFIC_SOURCES if source_entries is None else source_entries
    coverage_by_id = {item.source_id: item for item in coverage_entries}
    errors: list[str] = []

    expected_engine_ids = tuple(contract.engine_id for contract in engine_contract_catalog())
    expected = set(expected_engine_ids)
    seen: set[str] = set()
    for binding in entries:
        if binding.engine_id in seen:
            errors.append(f"ENGINE_SOURCE_DUPLICATE:{binding.engine_id}")
        seen.add(binding.engine_id)
        if binding.engine_id not in expected:
            errors.append(f"ENGINE_SOURCE_UNKNOWN_ENGINE:{binding.engine_id}")
        if binding.mode is EngineSourceMode.INDIRECT_REGISTRY and binding.source_ids:
            errors.append(f"ENGINE_SOURCE_INDIRECT_HAS_DIRECT_SOURCE:{binding.engine_id}")

        for source_id in binding.source_ids:
            source = source_map.get(source_id)
            if source is None:
                errors.append(f"ENGINE_SOURCE_UNKNOWN_SOURCE:{binding.engine_id}:{source_id}")
                continue
            coverage = coverage_by_id.get(source_id)
            if coverage is None:
                errors.append(f"ENGINE_SOURCE_UNCOVERED_SOURCE:{binding.engine_id}:{source_id}")
                continue
            if source.deprecated or coverage.status in {
                SourceOperationalStatus.HISTORICAL,
                SourceOperationalStatus.BLOCKED,
            }:
                errors.append(f"ENGINE_SOURCE_FORBIDDEN_SOURCE:{binding.engine_id}:{source_id}")
            if (
                binding.mode is EngineSourceMode.ADAPTER_QUERY
                and coverage.status is not SourceOperationalStatus.ADAPTER_QUERY
            ):
                errors.append(f"ENGINE_SOURCE_MODE_MISMATCH:{binding.engine_id}:{source_id}")
            if (
                binding.mode is EngineSourceMode.FORGE_HANDOFF
                and coverage.status is not SourceOperationalStatus.FORGE_HANDOFF
            ):
                errors.append(f"ENGINE_SOURCE_MODE_MISMATCH:{binding.engine_id}:{source_id}")

    missing = expected - seen
    errors.extend(f"ENGINE_SOURCE_MISSING_ENGINE:{engine_id}" for engine_id in sorted(missing))
    extra = seen - expected
    errors.extend(f"ENGINE_SOURCE_UNKNOWN_ENGINE:{engine_id}" for engine_id in sorted(extra))
    return EngineSourceMatrixAudit(entries, tuple(sorted(set(errors))))


__all__ = [
    "ENGINE_SOURCE_MATRIX",
    "EngineSourceBinding",
    "EngineSourceMatrixAudit",
    "EngineSourceMode",
    "audit_engine_source_matrix",
]
