"""Contrats publics du BFF GeoSylva serveur."""

from uuid import uuid4

import pytest

from gsie_api.geosylva.schemas import (
    GeoSylvaAnalysisRequest,
    GeoSylvaAnalysisStatus,
    canonical_request_fingerprint,
)


def _request_payload() -> dict[str, object]:
    return {
        "schema_version": "geosylva.analysis.request.v1",
        "request_id": str(uuid4()),
        "station_id": str(uuid4()),
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-0.75, 46.12],
                    [-0.74, 46.12],
                    [-0.74, 46.13],
                    [-0.75, 46.12],
                ]
            ],
        },
        "species_taxref_ids": [11612, 11614],
        "question": "Quelles limites stationnelles faut-il surveiller ?",
        "objective": "mixte",
        "requested_capabilities": [
            "reasoning",
            "diagnostic",
            "recommendation",
            "validation",
        ],
        "app_version": "3.0.0",
    }


def should_accept_bounded_wgs84_polygon_and_taxref_identifiers() -> None:
    request = GeoSylvaAnalysisRequest.model_validate(_request_payload())

    assert request.geometry.type == "Polygon"
    assert request.species_taxref_ids == [11612, 11614]
    assert request.status_initial == GeoSylvaAnalysisStatus.pending


def should_reject_geometry_outside_wgs84() -> None:
    payload = _request_payload()
    payload["geometry"] = {
        "type": "Polygon",
        "coordinates": [[[190.0, 46.0], [2.0, 46.0], [2.0, 47.0], [190.0, 46.0]]],
    }

    with pytest.raises(ValueError, match="WGS84"):
        GeoSylvaAnalysisRequest.model_validate(payload)


def should_reject_duplicate_taxref_identifiers() -> None:
    payload = _request_payload()
    payload["species_taxref_ids"] = [11612, 11612]

    with pytest.raises(ValueError, match="TAXREF.*uniques"):
        GeoSylvaAnalysisRequest.model_validate(payload)


def should_reject_unknown_capability() -> None:
    payload = _request_payload()
    payload["requested_capabilities"] = ["reasoning", "magic"]

    with pytest.raises(ValueError, match="requested_capabilities"):
        GeoSylvaAnalysisRequest.model_validate(payload)


def should_compute_same_fingerprint_for_equivalent_capability_order() -> None:
    payload = _request_payload()
    first = GeoSylvaAnalysisRequest.model_validate(payload)
    payload["requested_capabilities"] = list(reversed(first.requested_capabilities))
    second = GeoSylvaAnalysisRequest.model_validate(payload)

    assert canonical_request_fingerprint(first) == canonical_request_fingerprint(second)


def should_reject_more_than_geometry_budget() -> None:
    payload = _request_payload()
    ring = [[float(index % 180), 46.0] for index in range(10_001)]
    ring.append(ring[0])
    payload["geometry"] = {"type": "Polygon", "coordinates": [ring]}

    with pytest.raises(ValueError, match="10 000"):
        GeoSylvaAnalysisRequest.model_validate(payload)
