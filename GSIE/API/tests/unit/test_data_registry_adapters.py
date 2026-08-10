"""Contrat et registre de plugins des adapters RFC-0038 Phase 3."""

from datetime import UTC, datetime

import pytest

from gsie_api.data.adapters import (
    AdapterAlreadyRegisteredError,
    AdapterCapability,
    AdapterCapabilityError,
    AdapterContext,
    AdapterContractError,
    AdapterDatasetCandidate,
    AdapterDescriptor,
    AdapterDiscoveryRequest,
    AdapterFetchRequest,
    AdapterHealthReport,
    AdapterInstantiationError,
    AdapterNotFoundError,
    AdapterPluginRegistry,
    AdapterQueryRequest,
    AdapterQueryResult,
    AdapterSecurityError,
    DataSourceAdapter,
)
from gsie_api.infrastructure.models.enums import DatasetHealthStatus


def _descriptor(
    key: str = "fake-source",
    *,
    capabilities: frozenset[AdapterCapability] | None = None,
    domains: frozenset[str] | None = None,
) -> AdapterDescriptor:
    return AdapterDescriptor(
        key=key,
        name="Fournisseur de test",
        version="0.1.0",
        capabilities=capabilities
        or frozenset({AdapterCapability.HEALTH, AdapterCapability.DISCOVERY}),
        domains=domains or frozenset({"weather"}),
        endpoint="https://data.example.test/v1",
        allowlisted_hosts=frozenset({"data.example.test"}),
    )


class FakeAdapter(DataSourceAdapter):
    def __init__(self, descriptor: AdapterDescriptor | None = None) -> None:
        self._descriptor = descriptor or _descriptor()
        self.health_calls = 0

    @property
    def descriptor(self) -> AdapterDescriptor:
        return self._descriptor

    async def health(self, context: AdapterContext) -> AdapterHealthReport:
        self.health_calls += 1
        return AdapterHealthReport(
            adapter_key=self.descriptor.key,
            status=DatasetHealthStatus.healthy,
            checked_at=datetime.now(UTC),
        )

    async def discover(
        self, request: AdapterDiscoveryRequest, context: AdapterContext
    ) -> tuple[AdapterDatasetCandidate, ...]:
        del context
        return (
            AdapterDatasetCandidate(
                external_id="weather-1",
                title="Observation météo de test",
                version="2026-08",
                domain="weather",
                observed_at=datetime.now(UTC),
                distribution_url="https://data.example.test/weather-1",
                metadata={"source": "fixture"},
            ),
        )[: request.limit]


def test_descriptor_normalizes_and_requires_endpoint_allowlist() -> None:
    descriptor = AdapterDescriptor(
        key="  Test_Source ",
        name=" Test ",
        version=" 1.0 ",
        capabilities=frozenset({AdapterCapability.HEALTH}),
        endpoint="https://DATA.EXAMPLE.TEST/api",
        allowlisted_hosts=frozenset({"data.example.test."}),
    )

    assert descriptor.key == "test_source"
    assert descriptor.name == "Test"
    assert descriptor.endpoint == "https://DATA.EXAMPLE.TEST/api"
    assert descriptor.allowlisted_hosts == frozenset({"data.example.test"})


def test_descriptor_rejects_unsafe_or_incomplete_configuration() -> None:
    with pytest.raises(AdapterContractError, match="health"):
        AdapterDescriptor(
            key="source",
            name="Source",
            version="1",
            capabilities=frozenset({AdapterCapability.DISCOVERY}),
        )
    with pytest.raises(AdapterContractError, match="allowlisted_hosts"):
        AdapterDescriptor(
            key="source",
            name="Source",
            version="1",
            capabilities=frozenset({AdapterCapability.HEALTH}),
            endpoint="https://source.example.test/api",
        )
    with pytest.raises(AdapterContractError):
        AdapterDescriptor(
            key="source",
            name="Source",
            version="1",
            capabilities=frozenset({AdapterCapability.HEALTH}),
            domains=frozenset({"unknown-domain"}),
        )
    with pytest.raises(AdapterContractError):
        AdapterDescriptor(
            key="source",
            name="Source",
            version="1",
            capabilities=frozenset({AdapterCapability.HEALTH}),
            endpoint="https://user:password@source.example.test/api",
            allowlisted_hosts=frozenset({"source.example.test"}),
        )


def test_context_and_candidate_are_bounded_and_immutable() -> None:
    context = AdapterContext(trace_id="trace-001", timeout_seconds=5, max_bytes=1024)
    candidate = AdapterDatasetCandidate(
        external_id=" id ",
        title=" Titre ",
        version=" v1 ",
        domain="weather",
        observed_at=datetime.now(UTC),
        metadata={"key": "value"},
    )

    assert context.trace_id == "trace-001"
    assert candidate.external_id == "id"
    with pytest.raises(TypeError):
        candidate.metadata["other"] = "value"  # type: ignore[index]
    with pytest.raises(AdapterContractError):
        AdapterContext(trace_id="", timeout_seconds=5)
    with pytest.raises(AdapterContractError):
        AdapterContext(trace_id="trace", timeout_seconds=0)


def test_registry_is_lazy_deterministic_and_domain_aware() -> None:
    registry = AdapterPluginRegistry()
    created = 0

    def factory() -> FakeAdapter:
        nonlocal created
        created += 1
        return FakeAdapter()

    registry.register(_descriptor(), factory)
    assert created == 0
    assert [item.key for item in registry.descriptors()] == ["fake-source"]
    assert [item.key for item in registry.for_domain("weather")] == ["fake-source"]
    assert registry.capable(AdapterCapability.HEALTH)[0].key == "fake-source"

    adapter = registry.get("FAKE-SOURCE")
    assert registry.get("fake-source") is adapter
    assert created == 1

    with pytest.raises(AdapterAlreadyRegisteredError):
        registry.register(_descriptor(), factory)
    registry.remove("fake-source")
    with pytest.raises(AdapterNotFoundError):
        registry.get("fake-source")


def test_registry_rejects_factory_descriptor_mismatch() -> None:
    registry = AdapterPluginRegistry()
    registry.register(_descriptor("one"), lambda: FakeAdapter(_descriptor("two")))

    with pytest.raises(AdapterInstantiationError):
        registry.get("one")


@pytest.mark.asyncio
async def test_adapter_contract_supports_health_and_discovery_without_network() -> None:
    adapter = FakeAdapter()
    context = AdapterContext(trace_id="trace-002")
    report = await adapter.health(context)
    candidates = await adapter.discover(AdapterDiscoveryRequest(limit=1), context)

    assert report.status is DatasetHealthStatus.healthy
    assert candidates[0].domain == "weather"
    assert adapter.health_calls == 1


@pytest.mark.asyncio
async def test_undeclared_capability_is_rejected_explicitly() -> None:
    adapter = FakeAdapter()
    with pytest.raises(AdapterCapabilityError, match="query"):
        await adapter.query(AdapterQueryRequest(), AdapterContext(trace_id="trace-003"))


def test_egress_allowlist_and_fetch_contract_block_unsafe_urls() -> None:
    adapter = FakeAdapter()
    assert adapter.validate_target_url("https://data.example.test/data") == (
        "https://data.example.test/data"
    )
    with pytest.raises(AdapterSecurityError):
        adapter.validate_target_url("https://other.example.test/data")
    with pytest.raises(AdapterContractError):
        AdapterFetchRequest(
            external_id="dataset-1",
            distribution_url="file:///etc/passwd",
        )


def test_query_result_keeps_cursor_and_observation_timezone() -> None:
    result = AdapterQueryResult(
        items=({"value": 1},),
        observed_at=datetime.now(UTC),
        next_cursor="next",
    )
    request = AdapterQueryRequest(parameters={"q": "forest"}, limit=2, cursor="current")

    assert result.items[0]["value"] == 1
    assert request.parameters["q"] == "forest"
    with pytest.raises(AdapterContractError):
        AdapterQueryResult(items=(), observed_at=datetime(2026, 1, 1))
