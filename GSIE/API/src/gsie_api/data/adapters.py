"""Contrat commun des adapters Data Registry (RFC-0038, Phase 3).

Un adapter est le seul composant autorisé à ouvrir une connexion sortante vers
un fournisseur. Cette tranche ne fournit encore aucun adapter fournisseur :
elle stabilise le contrat, la vérification d'allowlist et le registre de
plugins sans effectuer de réseau ni de résolution de données.
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from gsie_api.data.contracts import normalize_slug, validate_domain

if TYPE_CHECKING:
    from gsie_api.infrastructure.models.enums import DatasetHealthStatus

_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_EXTERNAL_ID_MAX_LENGTH = 200
_MAX_DISCOVERY_LIMIT = 100
_DEFAULT_FETCH_MAX_BYTES = 32 * 1024 * 1024


class AdapterCapability(StrEnum):
    """Capacités qu'un plugin peut déclarer explicitement."""

    DISCOVERY = "discovery"
    METADATA = "metadata"
    HEALTH = "health"
    QUERY = "query"
    FETCH = "fetch"
    NORMALIZE = "normalize"


class AdapterError(RuntimeError):
    """Erreur racine stable du contrat d'adapter."""

    code = "ADAPTER_ERROR"


class AdapterContractError(AdapterError):
    """Configuration ou payload d'adapter invalide."""

    code = "ADAPTER_CONTRACT_INVALID"


class AdapterCapabilityError(AdapterError):
    """Capacité non déclarée par un adapter."""

    code = "ADAPTER_CAPABILITY_UNSUPPORTED"


class AdapterSecurityError(AdapterError):
    """Cible sortante absente de l'allowlist de l'adapter."""

    code = "ADAPTER_EGRESS_BLOCKED"


class AdapterRegistryError(AdapterError):
    """Erreur du registre de plugins."""

    code = "ADAPTER_REGISTRY_ERROR"


class AdapterAlreadyRegisteredError(AdapterRegistryError):
    """Une clé d'adapter est déjà enregistrée."""

    code = "ADAPTER_ALREADY_REGISTERED"


class AdapterNotFoundError(AdapterRegistryError):
    """La clé demandée n'est pas enregistrée."""

    code = "ADAPTER_NOT_FOUND"


class AdapterInstantiationError(AdapterRegistryError):
    """La factory d'un plugin n'a pas pu créer son adapter."""

    code = "ADAPTER_INSTANTIATION_FAILED"


def _raise_contract(message: str) -> None:
    raise AdapterContractError(message)


def _validate_public_url(value: str, *, field_name: str) -> str:
    """Valide une URL de fournisseur sans effectuer de résolution DNS.

    La protection SSRF complète reste portée par ``ResilientHttpClient`` au
    moment de l'appel. Ici, le contrat refuse déjà les schémas locaux, les
    identifiants et les query/fragment susceptibles de contenir une URL
    présignée ou un secret.
    """
    if not isinstance(value, str) or not value.strip():
        _raise_contract(f"{field_name} doit être une URL non vide")
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        _raise_contract(f"{field_name} doit utiliser http:// ou https://")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        _raise_contract(f"{field_name} ne doit contenir ni identifiant, ni query, ni fragment")
    return value.strip()


def _normalize_hosts(values: Iterable[str]) -> frozenset[str]:
    hosts: set[str] = set()
    for value in values:
        host = value.strip().lower().rstrip(".")
        if not host or ":" in host or "/" in host:
            _raise_contract("Une allowlist d'adapter ne peut contenir qu'un nom d'hôte")
        hosts.add(host)
    return frozenset(hosts)


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    """Identité déclarative et surface de sécurité d'un adapter."""

    key: str
    name: str
    version: str
    capabilities: frozenset[AdapterCapability]
    domains: frozenset[str] = frozenset()
    endpoint: str | None = None
    allowlisted_hosts: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        try:
            key = normalize_slug(self.key)
        except ValueError as exc:
            raise AdapterContractError(f"Clé d'adapter invalide : {exc}") from exc
        if not self.name.strip():
            raise AdapterContractError("Le nom d'adapter est obligatoire")
        if not self.version.strip():
            raise AdapterContractError("La version d'adapter est obligatoire")
        try:
            capabilities = frozenset(AdapterCapability(value) for value in self.capabilities)
        except ValueError as exc:
            raise AdapterContractError("Capacité d'adapter inconnue") from exc
        if AdapterCapability.HEALTH not in capabilities:
            raise AdapterContractError("Tout adapter doit déclarer la capacité health")
        try:
            domains = frozenset(validate_domain(value) for value in self.domains)
        except ValueError as exc:
            raise AdapterContractError(str(exc)) from exc
        hosts = _normalize_hosts(self.allowlisted_hosts)
        endpoint = self.endpoint
        if endpoint is not None:
            endpoint = _validate_public_url(endpoint, field_name="endpoint")
            endpoint_host = urlsplit(endpoint).hostname
            if endpoint_host is None or endpoint_host.lower().rstrip(".") not in hosts:
                raise AdapterContractError(
                    "L'hôte endpoint doit être présent dans allowlisted_hosts"
                )
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "domains", domains)
        object.__setattr__(self, "allowlisted_hosts", hosts)
        object.__setattr__(self, "endpoint", endpoint)


@dataclass(frozen=True, slots=True)
class AdapterContext:
    """Contexte borné transmis à chaque opération d'adapter."""

    trace_id: str
    timeout_seconds: float = 30.0
    max_bytes: int = _DEFAULT_FETCH_MAX_BYTES
    offline: bool = False

    def __post_init__(self) -> None:
        if not _TRACE_ID_PATTERN.fullmatch(self.trace_id.strip()):
            raise AdapterContractError("trace_id invalide")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise AdapterContractError("timeout_seconds doit être strictement positif")
        if self.max_bytes <= 0:
            raise AdapterContractError("max_bytes doit être strictement positif")
        object.__setattr__(self, "trace_id", self.trace_id.strip())


@dataclass(frozen=True, slots=True)
class AdapterHealthReport:
    """Résultat d'un contrôle de santé d'un fournisseur."""

    adapter_key: str
    status: DatasetHealthStatus
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float | None = None
    http_status: int | None = None
    observed_version: str | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        try:
            key = normalize_slug(self.adapter_key)
        except ValueError as exc:
            raise AdapterContractError(f"Clé d'adapter invalide : {exc}") from exc
        if self.checked_at.tzinfo is None:
            raise AdapterContractError("checked_at doit être horodaté avec un fuseau")
        if self.latency_ms is not None and (
            not math.isfinite(self.latency_ms) or self.latency_ms < 0
        ):
            raise AdapterContractError("latency_ms doit être nul ou positif")
        if self.http_status is not None and not 100 <= self.http_status <= 599:
            raise AdapterContractError("http_status doit être compris entre 100 et 599")
        object.__setattr__(self, "adapter_key", key)


@dataclass(frozen=True, slots=True)
class AdapterDiscoveryRequest:
    """Requête de découverte bornée, indépendante du resolver."""

    domains: frozenset[str] = frozenset()
    bbox: tuple[float, float, float, float] | None = None
    limit: int = 100
    cursor: str | None = None

    def __post_init__(self) -> None:
        try:
            domains = frozenset(validate_domain(value) for value in self.domains)
        except ValueError as exc:
            raise AdapterContractError(str(exc)) from exc
        if not 1 <= self.limit <= _MAX_DISCOVERY_LIMIT:
            raise AdapterContractError(f"limit doit être compris entre 1 et {_MAX_DISCOVERY_LIMIT}")
        if self.bbox is not None:
            min_lon, min_lat, max_lon, max_lat = self.bbox
            if not (-180 <= min_lon <= max_lon <= 180):
                raise AdapterContractError("La bbox doit respecter les longitudes WGS84")
            if not (-90 <= min_lat <= max_lat <= 90):
                raise AdapterContractError("La bbox doit respecter les latitudes WGS84")
        if self.cursor is not None and (not self.cursor.strip() or len(self.cursor) > 512):
            raise AdapterContractError("cursor invalide")
        object.__setattr__(self, "domains", domains)
        object.__setattr__(self, "cursor", self.cursor.strip() if self.cursor else None)


@dataclass(frozen=True, slots=True)
class AdapterDatasetCandidate:
    """Candidat découvert, encore non promu dans le Registry."""

    external_id: str
    title: str
    version: str
    domain: str
    observed_at: datetime
    licence: str | None = None
    distribution_url: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        external_id = self.external_id.strip()
        if not external_id or len(external_id) > _EXTERNAL_ID_MAX_LENGTH:
            raise AdapterContractError("external_id invalide")
        if not self.title.strip() or not self.version.strip():
            raise AdapterContractError("title et version sont obligatoires")
        try:
            domain = validate_domain(self.domain)
        except ValueError as exc:
            raise AdapterContractError(str(exc)) from exc
        if self.observed_at.tzinfo is None:
            raise AdapterContractError("observed_at doit être horodaté avec un fuseau")
        distribution_url = (
            _validate_public_url(self.distribution_url, field_name="distribution_url")
            if self.distribution_url is not None
            else None
        )
        object.__setattr__(self, "external_id", external_id)
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "distribution_url", distribution_url)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class AdapterQueryRequest:
    """Requête fournisseur explicite, sans notion de sélection automatique."""

    parameters: Mapping[str, object] = field(default_factory=dict)
    limit: int = 100
    cursor: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= _MAX_DISCOVERY_LIMIT:
            raise AdapterContractError(f"limit doit être compris entre 1 et {_MAX_DISCOVERY_LIMIT}")
        if self.cursor is not None and (not self.cursor.strip() or len(self.cursor) > 512):
            raise AdapterContractError("cursor invalide")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        object.__setattr__(self, "cursor", self.cursor.strip() if self.cursor else None)


@dataclass(frozen=True, slots=True)
class AdapterQueryResult:
    """Résultat brut borné d'une requête adapter."""

    items: tuple[Mapping[str, object], ...]
    observed_at: datetime
    next_cursor: str | None = None

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise AdapterContractError("observed_at doit être horodaté avec un fuseau")
        if self.next_cursor is not None and (
            not self.next_cursor.strip() or len(self.next_cursor) > 512
        ):
            raise AdapterContractError("next_cursor invalide")
        normalized = tuple(MappingProxyType(dict(item)) for item in self.items)
        object.__setattr__(self, "items", normalized)
        object.__setattr__(
            self, "next_cursor", self.next_cursor.strip() if self.next_cursor else None
        )


@dataclass(frozen=True, slots=True)
class AdapterFetchRequest:
    """Demande de fetch soumise aux bornes de taille et d'URL."""

    external_id: str
    distribution_url: str
    max_bytes: int = _DEFAULT_FETCH_MAX_BYTES
    expected_checksum: str | None = None
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.external_id.strip():
            raise AdapterContractError("external_id obligatoire pour un fetch")
        _validate_public_url(self.distribution_url, field_name="distribution_url")
        if self.max_bytes <= 0:
            raise AdapterContractError("max_bytes doit être strictement positif")
        if self.expected_checksum is not None and not re.fullmatch(
            r"[0-9a-fA-F]{64}", self.expected_checksum
        ):
            raise AdapterContractError("expected_checksum doit être un SHA-256 hexadécimal")
        object.__setattr__(self, "external_id", self.external_id.strip())
        object.__setattr__(self, "distribution_url", self.distribution_url.strip())
        object.__setattr__(
            self,
            "expected_checksum",
            self.expected_checksum.lower() if self.expected_checksum is not None else None,
        )
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))


@dataclass(frozen=True, slots=True)
class AdapterFetchResult:
    """Flux de bytes ; le contenu n'est jamais chargé en mémoire par contrat."""

    body: AsyncIterator[bytes]
    content_type: str | None = None
    content_length: int | None = None

    def __post_init__(self) -> None:
        if self.content_length is not None and self.content_length < 0:
            raise AdapterContractError("content_length ne peut pas être négatif")


AdapterFactory = Callable[[], "DataSourceAdapter"]


class DataSourceAdapter(ABC):
    """Façade commune des fournisseurs externes.

    Les méthodes par défaut refusent l'opération si la capacité n'est pas
    déclarée. Cela évite qu'un plugin incomplet simule silencieusement une
    découverte, un fetch ou une normalisation.
    """

    @property
    @abstractmethod
    def descriptor(self) -> AdapterDescriptor:
        """Identité statique et capacités du plugin."""
        raise NotImplementedError

    def supports(self, capability: AdapterCapability) -> bool:
        return capability in self.descriptor.capabilities

    def validate_target_url(self, url: str) -> str:
        """Vérifie l'URL et l'allowlist avant le client HTTP résilient."""
        normalized = _validate_public_url(url, field_name="target_url")
        hostname = urlsplit(normalized).hostname
        if (
            hostname is None
            or hostname.lower().rstrip(".") not in self.descriptor.allowlisted_hosts
        ):
            raise AdapterSecurityError("ADAPTER_EGRESS_BLOCKED: hôte absent de l'allowlist")
        return normalized

    def _require(self, capability: AdapterCapability) -> None:
        if not self.supports(capability):
            raise AdapterCapabilityError(
                f"{self.descriptor.key} ne déclare pas la capacité {capability.value}"
            )

    async def health(self, context: AdapterContext) -> AdapterHealthReport:
        del context
        self._require(AdapterCapability.HEALTH)
        raise AdapterCapabilityError(f"{self.descriptor.key} n'implémente pas health")

    async def discover(
        self, request: AdapterDiscoveryRequest, context: AdapterContext
    ) -> tuple[AdapterDatasetCandidate, ...]:
        del request, context
        self._require(AdapterCapability.DISCOVERY)
        raise AdapterCapabilityError(f"{self.descriptor.key} n'implémente pas discovery")

    async def query(
        self, request: AdapterQueryRequest, context: AdapterContext
    ) -> AdapterQueryResult:
        del request, context
        self._require(AdapterCapability.QUERY)
        raise AdapterCapabilityError(f"{self.descriptor.key} n'implémente pas query")

    async def fetch(
        self, request: AdapterFetchRequest, context: AdapterContext
    ) -> AdapterFetchResult:
        del request, context
        self._require(AdapterCapability.FETCH)
        raise AdapterCapabilityError(f"{self.descriptor.key} n'implémente pas fetch")

    def normalize(self, result: AdapterQueryResult) -> tuple[Mapping[str, object], ...]:
        del result
        self._require(AdapterCapability.NORMALIZE)
        raise AdapterCapabilityError(f"{self.descriptor.key} n'implémente pas normalize")


@dataclass(frozen=True, slots=True)
class AdapterPlugin:
    """Enregistrement lazy d'une factory ; aucun réseau à l'inscription."""

    descriptor: AdapterDescriptor
    factory: AdapterFactory


class AdapterPluginRegistry:
    """Registre explicite et déterministe de plugins Data Registry."""

    def __init__(self, plugins: Iterable[AdapterPlugin] = ()) -> None:
        self._plugins: dict[str, AdapterPlugin] = {}
        self._instances: dict[str, DataSourceAdapter] = {}
        for plugin in plugins:
            self.register(plugin.descriptor, plugin.factory)

    def register(
        self,
        descriptor: AdapterDescriptor,
        factory: AdapterFactory,
        *,
        replace: bool = False,
    ) -> None:
        """Ajoute une factory sans l'instancier ni contacter son fournisseur."""
        if not callable(factory):
            raise AdapterContractError("La factory d'adapter doit être appelable")
        if descriptor.key in self._plugins and not replace:
            raise AdapterAlreadyRegisteredError(f"Adapter déjà enregistré : {descriptor.key}")
        self._plugins[descriptor.key] = AdapterPlugin(descriptor, factory)
        self._instances.pop(descriptor.key, None)

    def register_instance(self, adapter: DataSourceAdapter, *, replace: bool = False) -> None:
        """Enregistre une instance déjà construite, utile pour un bootstrap contrôlé."""
        descriptor = adapter.descriptor
        self.register(descriptor, lambda: adapter, replace=replace)

    def get(self, key: str) -> DataSourceAdapter:
        """Construit à la demande l'instance d'un plugin enregistré."""
        try:
            normalized_key = normalize_slug(key)
        except ValueError as exc:
            raise AdapterNotFoundError(f"Clé d'adapter invalide : {key}") from exc
        plugin = self._plugins.get(normalized_key)
        if plugin is None:
            raise AdapterNotFoundError(f"Adapter inconnu : {normalized_key}")
        cached = self._instances.get(normalized_key)
        if cached is not None:
            return cached
        try:
            adapter = plugin.factory()
        except Exception as exc:
            raise AdapterInstantiationError(
                f"Impossible d'instancier l'adapter {normalized_key}"
            ) from exc
        if adapter.descriptor != plugin.descriptor:
            raise AdapterInstantiationError(
                f"La factory {normalized_key} renvoie un descriptor différent"
            )
        self._instances[normalized_key] = adapter
        return adapter

    def descriptors(self) -> tuple[AdapterDescriptor, ...]:
        """Retourne les descriptors dans un ordre stable, sans instanciation."""
        return tuple(self._plugins[key].descriptor for key in sorted(self._plugins))

    def for_domain(self, domain: str) -> tuple[AdapterDescriptor, ...]:
        """Retourne les plugins déclarant un domaine ou une portée globale."""
        try:
            normalized_domain = validate_domain(domain)
        except ValueError as exc:
            raise AdapterContractError(str(exc)) from exc
        return tuple(
            descriptor
            for descriptor in self.descriptors()
            if not descriptor.domains or normalized_domain in descriptor.domains
        )

    def capable(self, capability: AdapterCapability) -> tuple[AdapterDescriptor, ...]:
        """Retourne les plugins déclarant une capacité donnée."""
        return tuple(
            descriptor for descriptor in self.descriptors() if capability in descriptor.capabilities
        )

    def remove(self, key: str) -> None:
        """Retire explicitement un plugin du registre de bootstrap."""
        try:
            normalized_key = normalize_slug(key)
        except ValueError as exc:
            raise AdapterNotFoundError(f"Clé d'adapter invalide : {key}") from exc
        if self._plugins.pop(normalized_key, None) is None:
            raise AdapterNotFoundError(f"Adapter inconnu : {normalized_key}")
        self._instances.pop(normalized_key, None)


__all__ = [
    "AdapterAlreadyRegisteredError",
    "AdapterCapability",
    "AdapterCapabilityError",
    "AdapterContext",
    "AdapterContractError",
    "AdapterDatasetCandidate",
    "AdapterDescriptor",
    "AdapterDiscoveryRequest",
    "AdapterError",
    "AdapterFactory",
    "AdapterFetchRequest",
    "AdapterFetchResult",
    "AdapterHealthReport",
    "AdapterInstantiationError",
    "AdapterNotFoundError",
    "AdapterPlugin",
    "AdapterPluginRegistry",
    "AdapterQueryRequest",
    "AdapterQueryResult",
    "AdapterRegistryError",
    "AdapterSecurityError",
    "DataSourceAdapter",
]
