#!/usr/bin/env python3
"""Test d'intégration réel de la chaîne Data Registry.

Le test contacte les quatre fournisseurs déclarés par le bootstrap, vérifie la
santé puis la requête, normalise le résultat, l'archive temporairement dans le
stockage objet configuré, relit l'objet avec contrôle d'empreinte et soumet la
projection au Data Selection Engine. Aucun jeu de données simulé n'est utilisé.

Le test est volontairement borné : un taxon, un point IGN, un profil SoilGrids
et la carte départementale Météo-France. Les objets sont supprimés à la fin,
sauf avec ``--keep-objects`` pour une inspection opérateur explicite.

Dans Docker, exécuter le contenu de ce fichier dans le conteneur API avec le
certificat de confiance de l'environnement d'entreprise déjà préparé :
``SSL_CERT_FILE=/tmp/gsie-e2e-ca.pem``. La validation TLS ne doit jamais être
désactivée.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import sys
import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from gsie_api.data.adapters import (  # type: ignore[import-untyped]
    AdapterContext,
    AdapterQueryRequest,
)
from gsie_api.data.bootstrap import build_adapter_registry  # type: ignore[import-untyped]
from gsie_api.data.contracts import DOMAIN_VOCABULARY_VERSION  # type: ignore[import-untyped]
from gsie_api.data.resolver import (  # type: ignore[import-untyped]
    ResolutionMetadata,
    resolve_candidates,
)
from gsie_api.data.schemas import (  # type: ignore[import-untyped]
    DataSearchQuery,
    DatasetSummary,
    DatasetVersionRead,
    SearchCandidate,
)
from gsie_api.infrastructure.models.enums import (  # type: ignore[import-untyped]
    DatasetPurpose,
    DatasetStatus,
    EvidenceLevel,
)
from gsie_api.infrastructure.object_storage import (  # type: ignore[import-untyped]
    get_object_storage,
)

_ADAPTER_KEYS = ("gbif", "ign", "soilgrids", "meteofrance")
_REQUESTS = {
    "gbif": AdapterQueryRequest(
        parameters={"operation": "species_match", "name": "Quercus robur"},
        limit=1,
    ),
    "ign": AdapterQueryRequest(
        parameters={
            "operation": "altitude",
            "latitude": 48.8566,
            "longitude": 2.3522,
        },
        limit=1,
    ),
    # Paris intra-muros peut ne pas avoir de couche SoilGrids exploitable.
    # Ce point agricole français est couvert et reste dans le périmètre France.
    "soilgrids": AdapterQueryRequest(
        parameters={
            "operation": "properties",
            "latitude": 48.2,
            "longitude": 2.2,
            "properties": ["phh2o", "clay", "sand", "silt"],
            "depth": "0-5cm",
        },
        limit=1,
    ),
    "meteofrance": AdapterQueryRequest(
        parameters={"operation": "danger_feux_departements"},
        limit=100,
    ),
}


class E2ETestError(RuntimeError):
    """Erreur explicite de la campagne réelle."""


def _consume_normalized(key: str, rows: tuple[dict[str, Any], ...]) -> dict[str, object]:
    """Fait passer la sortie normalisée dans une projection métier minimale."""
    if not rows:
        raise E2ETestError(f"{key}: la normalisation ne contient aucune ligne")
    first = rows[0]
    if key == "gbif":
        usage_key = first.get("usageKey")
        if isinstance(usage_key, bool) or not isinstance(usage_key, int):
            raise E2ETestError("gbif: usageKey non entier après normalisation")
        return {"usage_key": usage_key, "scientific_name": first.get("scientificName")}
    if key == "ign":
        try:
            altitude = float(first["altitude_m"])
        except (KeyError, TypeError, ValueError) as exc:
            raise E2ETestError("ign: altitude_m inexploitable") from exc
        if not math.isfinite(altitude):
            raise E2ETestError("ign: altitude_m non finie")
        return {
            "altitude_m": altitude,
            "latitude": first.get("latitude"),
            "longitude": first.get("longitude"),
        }
    if key == "soilgrids":
        try:
            profile: dict[str, object] = {name: float(value) for name, value in first.items()}
        except (TypeError, ValueError) as exc:
            raise E2ETestError("soilgrids: profil non numérique") from exc
        phh2o = profile.get("phh2o")
        if isinstance(phh2o, float) and not 0 <= phh2o <= 14:
            raise E2ETestError("soilgrids: pH hors de [0, 14]")
        for name in ("clay", "sand", "silt"):
            value = profile.get(name)
            if isinstance(value, float) and not 0 <= value <= 100:
                raise E2ETestError(f"soilgrids: {name} hors de [0, 100]")
        return profile
    if not any(row.get("dep_code") for row in rows):
        raise E2ETestError("meteofrance: aucun département normalisé")
    return {
        "department_count": len(rows),
        "first_department": first.get("dep_code"),
        "first_level": first.get("niveau_j1"),
    }


def _resolver_projection(
    key: str,
    domain: str,
    checksum: str,
    item_count: int,
    byte_count: int,
    observed_at: datetime,
    trace_id: str,
) -> dict[str, object]:
    """Construit une projection éphémère et vérifie la sélection déterministe."""
    dataset_id = uuid.uuid4()
    version_id = uuid.uuid4()
    candidate = SearchCandidate(
        dataset=DatasetSummary(
            id=dataset_id,
            slug=f"e2e-{key}",
            title=f"E2E {key}",
            description="Projection éphémère du test fournisseur réel",
            publisher_id=None,
            purpose=DatasetPurpose.reference,
            topic=key,
            primary_domain=domain,
            domains=[domain],
            tags=["e2e"],
            domain_vocabulary_version=DOMAIN_VOCABULARY_VERSION,
        ),
        version=DatasetVersionRead(
            id=version_id,
            dataset_id=dataset_id,
            version="e2e",
            release_date=observed_at,
            temporal_coverage_start=None,
            temporal_coverage_end=None,
            changes=None,
            schema_hash=checksum,
            stats={
                "quality_score": 1.0,
                "stored_bytes": byte_count,
                "normalized_items": item_count,
            },
            status=DatasetStatus.production,
            evidence_level=EvidenceLevel.b,
            evidence_basis={"test": "real-provider"},
            evidence_assessed_at=observed_at,
            distributions=[],
        ),
    )
    response = resolve_candidates(
        DataSearchQuery(
            theme=domain,
            use="display",
            prefer=["freshness", "quality", "offline_availability"],
            limit=1,
        ),
        [candidate],
        metadata={
            version_id: ResolutionMetadata(
                quality_score=1.0,
                freshness_at=observed_at,
                offline_available=True,
            )
        },
        trace_id=trace_id,
        vocabulary_version=DOMAIN_VOCABULARY_VERSION,
        now=observed_at,
    )
    if response.selected is None or not response.selected.eligible:
        raise E2ETestError(f"{key}: le resolver n'a sélectionné aucune projection")
    return {"selected": True, "policy": response.policy_version}


async def run(*, trace_id: str, keep_objects: bool) -> dict[str, object]:
    """Exécute la campagne et retourne un rapport JSON sans secret."""
    registry = build_adapter_registry()
    storage = get_object_storage()
    context = AdapterContext(
        trace_id=trace_id,
        timeout_seconds=30,
        max_bytes=4 * 1024 * 1024,
    )
    run_id = uuid.uuid4().hex
    object_keys: list[str] = []
    adapters_report: dict[str, dict[str, object]] = {}
    report: dict[str, object] = {
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "adapters": adapters_report,
    }
    cleanup_failures: list[str] = []
    try:
        for key in _ADAPTER_KEYS:
            adapter = registry.get(key)
            health = await adapter.health(context)
            if health.status.value != "healthy":
                raise E2ETestError(
                    f"{key}: fournisseur indisponible ({health.status.value}, {health.error_code})"
                )
            result = await adapter.query(_REQUESTS[key], context)
            normalized = adapter.normalize(result)
            rows = tuple(dict(item) for item in normalized)
            consumed = _consume_normalized(key, rows)
            body = json.dumps(
                {
                    "adapter": key,
                    "observed_at": result.observed_at.isoformat(),
                    "items": rows,
                },
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
            checksum = hashlib.sha256(body).hexdigest()
            object_key = f"e2e/registry/{run_id}/{key}.json"
            uri = await storage.put(object_key, BytesIO(body), content_type="application/json")
            object_keys.append(object_key)
            head = await storage.head(object_key)
            downloaded = await storage.get(object_key)
            try:
                roundtrip = downloaded.read()
            finally:
                downloaded.close()
            if roundtrip != body or hashlib.sha256(roundtrip).hexdigest() != checksum:
                raise E2ETestError(f"{key}: checksum ou lecture stockage incohérent")
            domain = sorted(adapter.descriptor.domains)[0]
            resolver = _resolver_projection(
                key,
                domain,
                checksum,
                len(rows),
                len(body),
                result.observed_at,
                trace_id,
            )
            stored_length = head.get("ContentLength", head.get("content_length"))
            adapters_report[key] = {
                "health": health.status.value,
                "items": len(result.items),
                "normalized_items": len(rows),
                "stored_uri": uri,
                "bytes": len(body),
                "storage_content_length": stored_length,
                "sha256": checksum,
                "roundtrip": True,
                "consumer": consumed,
                "resolver": resolver,
            }
            print(
                f"PASS {key}: items={len(rows)} bytes={len(body)} "
                f"sha256={checksum[:16]} resolver=selected"
            )
    finally:
        if not keep_objects:
            for object_key in object_keys:
                try:
                    await storage.delete(object_key)
                except Exception:
                    cleanup_failures.append(object_key)
        await storage.close()
    report["cleanup"] = "kept" if keep_objects else ("ok" if not cleanup_failures else "failed")
    if cleanup_failures:
        raise E2ETestError("Objets de test non supprimés : " + ", ".join(cleanup_failures))
    report["finished_at"] = datetime.now(UTC).isoformat()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-id", default="e2e-data-20260810")
    parser.add_argument(
        "--keep-objects",
        action="store_true",
        help="conserver les objets e2e dans le stockage pour inspection opérateur",
    )
    args = parser.parse_args()
    try:
        report = asyncio.run(run(trace_id=args.trace_id, keep_objects=args.keep_objects))
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("REPORT " + json.dumps(report, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
