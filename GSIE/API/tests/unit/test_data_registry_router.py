"""Contrat HTTP et barrières du Data Registry."""

from gsie_api.app import create_app
from gsie_api.data.service import _safe_url


def should_register_all_phase_two_registry_routes() -> None:
    paths = {route.path for route in create_app().routes}
    assert {
        "/api/v1/data/catalog",
        "/api/v1/data/datasets/{dataset_id}",
        "/api/v1/data/providers",
        "/api/v1/data/search",
        "/api/v1/data/resolve",
        "/api/v1/data/health",
        "/api/v1/data/coverage",
    }.issubset(paths)


def should_never_expose_local_or_presigned_distribution_urls() -> None:
    assert _safe_url("local:///tmp/dataset.parquet") is None
    assert _safe_url("s3://private-bucket/object.parquet") is None
    assert _safe_url("https://example.test/object.parquet?X-Amz-Signature=secret") is None
    assert _safe_url("https://example.test/object.parquet") == "https://example.test/object.parquet"
