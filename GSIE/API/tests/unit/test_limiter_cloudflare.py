"""Tests du calcul de quota derrière Cloudflare Tunnel."""

from unittest.mock import patch

import pytest
from starlette.requests import Request

from gsie_api.core import limiter as limiter_module


def _request(*, peer: str = "172.20.0.5", connecting_ip: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if connecting_ip is not None:
        headers.append((b"cf-connecting-ip", connecting_ip.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": headers,
            "client": (peer, 12345),
            "server": ("api", 8000),
            "scheme": "http",
            "query_string": b"",
        }
    )


def should_ignore_cloudflare_header_in_direct_mode() -> None:
    with patch.object(limiter_module._settings, "edge_proxy_mode", "direct"):
        assert (
            limiter_module.get_client_address(_request(connecting_ip="203.0.113.10"))
            == "172.20.0.5"
        )


@pytest.mark.parametrize("address", ["203.0.113.10", "2001:db8::42"])
def should_use_canonical_cloudflare_address_in_tunnel_mode(address: str) -> None:
    with patch.object(limiter_module._settings, "edge_proxy_mode", "cloudflare_tunnel"):
        assert limiter_module.get_client_address(_request(connecting_ip=address)) == address


def should_fall_back_to_network_peer_for_invalid_cloudflare_address() -> None:
    with patch.object(limiter_module._settings, "edge_proxy_mode", "cloudflare_tunnel"):
        assert (
            limiter_module.get_client_address(_request(connecting_ip="203.0.113.10, 198.51.100.5"))
            == "172.20.0.5"
        )


def should_fall_back_to_network_peer_when_cloudflare_header_is_missing() -> None:
    with patch.object(limiter_module._settings, "edge_proxy_mode", "cloudflare_tunnel"):
        assert limiter_module.get_client_address(_request()) == "172.20.0.5"
