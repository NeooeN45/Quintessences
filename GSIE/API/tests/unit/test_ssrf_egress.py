"""Tests unitaires — Protection SSRF egress (RFC-0021 §4.3).

Couvre :
- valider_url_egress() : IP littérale privée, loopback, link-local, multicast, reserved
- valider_url_egress() : hostname résolvant vers une IP privée (DNS rebinding)
- valider_url_egress() : URL relative sans hostname (pas de risque)
- valider_url_egress() : hostname public autorisé
- ResilientHttpClient._request() : lève exception_class sur URL bloquée
- ResilientHttpClient._request() : requête normale sur URL publique

Utilise respx pour mocker le réseau et monkeypatch le résolveur DNS.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from gsie_api.shared import http_client
from gsie_api.shared.http_client import ResilientHttpClient, valider_url_egress

# ---------------------------------------------------------------------------
# valider_url_egress — IP littérales
# ---------------------------------------------------------------------------


class TestValiderUrlEgressIpLitterales:
    """valider_url_egress() avec des IPs littérales dans l'URL."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://127.0.0.1:8080/",
            "http://127.255.255.255/",
            "http://[::1]/",
        ],
    )
    def should_block_loopback_ip(self, url: str) -> None:
        with pytest.raises(ValueError, match="SSRF"):
            valider_url_egress(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",
            "http://169.254.0.1/",
            "http://[fe80::1]/",
        ],
    )
    def should_block_link_local_ip(self, url: str) -> None:
        with pytest.raises(ValueError, match="SSRF"):
            valider_url_egress(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://10.0.0.1/",
            "http://10.255.255.255/",
            "http://172.16.0.1/",
            "http://172.31.255.255/",
            "http://192.168.1.1/",
            "http://192.168.0.0/",
            "http://[fc00::1]/",
            "http://[fd00::1]/",
        ],
    )
    def should_block_private_ip(self, url: str) -> None:
        with pytest.raises(ValueError, match="SSRF"):
            valider_url_egress(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://0.0.0.0/",
            "http://[::]/",
        ],
    )
    def should_block_unspecified_ip(self, url: str) -> None:
        with pytest.raises(ValueError, match="SSRF"):
            valider_url_egress(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://224.0.0.1/",
            "http://239.255.255.255/",
        ],
    )
    def should_block_multicast_ip(self, url: str) -> None:
        with pytest.raises(ValueError, match="SSRF"):
            valider_url_egress(url)


# ---------------------------------------------------------------------------
# valider_url_egress — Hostnames (résolution DNS)
# ---------------------------------------------------------------------------


class TestValiderUrlEgressDnsResolution:
    """valider_url_egress() avec hostnames résolus via _dns_resolver."""

    def should_block_hostname_resolving_to_private_ip(self) -> None:
        """Un hostname public qui résout vers une IP privée est bloqué (DNS rebinding)."""
        with (
            patch.object(http_client, "_dns_resolver", return_value=["10.0.0.5"]),
            pytest.raises(ValueError, match="SSRF"),
        ):
            valider_url_egress("http://example.com/")

    def should_block_hostname_resolving_to_loopback(self) -> None:
        with (
            patch.object(http_client, "_dns_resolver", return_value=["127.0.0.1"]),
            pytest.raises(ValueError, match="SSRF"),
        ):
            valider_url_egress("http://example.com/")

    def should_block_hostname_resolving_to_link_local(self) -> None:
        with (
            patch.object(http_client, "_dns_resolver", return_value=["169.254.169.254"]),
            pytest.raises(ValueError, match="SSRF"),
        ):
            valider_url_egress("http://example.com/")

    def should_allow_hostname_resolving_to_public_ip(self) -> None:
        """Un hostname qui résout vers une IP publique est autorisé."""
        with patch.object(http_client, "_dns_resolver", return_value=["93.184.216.34"]):
            valider_url_egress("http://example.com/")  # ne lève pas

    def should_allow_hostname_with_empty_dns_resolution(self) -> None:
        """Un hostname qui ne résout pas (liste vide) est autorisé (fail-open DNS)."""
        with patch.object(http_client, "_dns_resolver", return_value=[]):
            valider_url_egress("http://nonexistent.example/")  # ne lève pas


# ---------------------------------------------------------------------------
# valider_url_egress — Cas particuliers
# ---------------------------------------------------------------------------


class TestValiderUrlEgressEdgeCases:
    """valider_url_egress() — cas particuliers."""

    def should_allow_relative_url_without_hostname(self) -> None:
        """Une URL relative sans hostname ne lève pas (pas de risque SSRF)."""
        valider_url_egress("/api/v1/data")  # ne lève pas

    def should_allow_url_without_scheme(self) -> None:
        """Une URL sans schéma ne lève pas si pas de hostname."""
        valider_url_egress("example.com/path")  # ne lève pas

    def should_allow_public_ip_literal(self) -> None:
        """Un littéral IP public est autorisé."""
        valider_url_egress("http://93.184.216.34/")  # ne lève pas

    def should_allow_https_public_hostname(self) -> None:
        """Un hostname public en HTTPS est autorisé."""
        with patch.object(http_client, "_dns_resolver", return_value=["93.184.216.34"]):
            valider_url_egress("https://api.example.com/v1/data")  # ne lève pas


# ---------------------------------------------------------------------------
# ResilientHttpClient._request — Intégration de la garde SSRF
# ---------------------------------------------------------------------------


class _FakeClient(ResilientHttpClient):
    """Client minimal pour tester la garde SSRF dans _request()."""

    @property
    def exception_class(self) -> type[Exception]:
        return RuntimeError

    @property
    def base_url(self) -> str:
        return "https://api.example.com"


class TestResilientHttpClientSsrfIntegration:
    """ResilientHttpClient._request() — la garde SSRF est intégrée."""

    async def should_raise_exception_class_on_ssrf_block(self) -> None:
        """Une URL vers 169.254.169.254 lève exception_class avec 'SSRF'."""
        client = _FakeClient(max_retries=0)
        with pytest.raises(RuntimeError, match="SSRF"):
            await client._request("GET", "http://169.254.169.254/latest/meta-data/")

    async def should_raise_exception_class_on_private_ip(self) -> None:
        """Une URL vers 10.0.0.1 lève exception_class."""
        client = _FakeClient(max_retries=0)
        with pytest.raises(RuntimeError, match="SSRF"):
            await client._request("GET", "http://10.0.0.1/")

    async def should_raise_exception_class_on_loopback(self) -> None:
        """Une URL vers 127.0.0.1 lève exception_class."""
        client = _FakeClient(max_retries=0)
        with pytest.raises(RuntimeError, match="SSRF"):
            await client._request("GET", "http://127.0.0.1/")

    async def should_raise_on_dns_rebinding(self) -> None:
        """Un hostname qui résout vers une IP privée lève exception_class."""
        client = _FakeClient(max_retries=0)
        with (
            patch.object(http_client, "_dns_resolver", return_value=["10.0.0.5"]),
            pytest.raises(RuntimeError, match="SSRF"),
        ):
            await client._request("GET", "http://internal.example.com/")

    @respx.mock
    async def should_allow_request_to_public_url(self) -> None:
        """Une URL publique passe la garde et effectue la requête."""
        respx.get("https://api.example.com/v1/data").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        client = _FakeClient(max_retries=0)
        with patch.object(http_client, "_dns_resolver", return_value=["93.184.216.34"]):
            response = await client._request("GET", "/v1/data")
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    @respx.mock
    async def should_allow_absolute_public_url(self) -> None:
        """Une URL absolue publique passe la garde."""
        respx.get("https://api.other.com/data").mock(return_value=httpx.Response(200, text="ok"))
        client = _FakeClient(max_retries=0)
        with patch.object(http_client, "_dns_resolver", return_value=["93.184.216.34"]):
            response = await client._request("GET", "https://api.other.com/data")
        assert response.status_code == 200
