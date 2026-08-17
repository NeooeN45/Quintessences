"""Tests du cloisonnement déclaratif des environnements de données."""

from gsie_api.core.data_environment import validate_data_environment


def test_test_environment_isolated() -> None:
    assert (
        validate_data_environment(
            environment="development",
            database_role="test",
            namespace="gsie-test",
            database_url="postgresql+asyncpg://gsie_api:x@localhost:5432/gsie_test",
            object_bucket="gsie-assets-test",
            compose_project="gsie-test",
        )
        == []
    )


def test_production_cannot_reuse_staging_namespace() -> None:
    errors = validate_data_environment(
        environment="production",
        database_role="production",
        namespace="gsie-staging",
        database_url="postgresql+asyncpg://gsie_api:x@db:5432/gsie_production",
        object_bucket="gsie-assets-production",
        compose_project="gsie-production",
    )

    assert "namespace non dédié au rôle" in errors


def test_benchmark_cannot_reuse_development_database() -> None:
    errors = validate_data_environment(
        environment="development",
        database_role="benchmark",
        namespace="gsie-benchmark",
        database_url="postgresql+asyncpg://gsie_api:x@localhost:5432/gsie",
        object_bucket="gsie-assets-benchmark",
        compose_project="gsie-benchmark",
    )

    assert "nom PostgreSQL non dédié au rôle" in errors
