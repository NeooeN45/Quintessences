"""Tests du SDK Python GSIE — conventions API : respx, pytest-asyncio auto."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
import pytest
import respx

from gsie_sdk import APIError, AuthenticationError, GSIEClient, TokenRefreshError

BASE_URL = "http://gsie.test"
API = f"{BASE_URL}/api/v1"


@pytest.fixture
async def client() -> AsyncGenerator[GSIEClient, None]:
    async with GSIEClient(BASE_URL) as c:
        yield c


@respx.mock
async def test_login_should_store_tokens_when_credentials_valid(client: GSIEClient) -> None:
    respx.post(f"{API}/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "access-abc",
                "refresh_token": "refresh-xyz",
                "token_type": "Bearer",
                "expires_in": 900,
            },
        )
    )
    await client.login("admin", "secret")
    assert client.is_authenticated


@respx.mock
async def test_login_should_raise_auth_error_when_credentials_invalid(client: GSIEClient) -> None:
    respx.post(f"{API}/auth/login").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthenticationError):
        await client.login("admin", "wrong")


@respx.mock
async def test_request_should_send_bearer_header_when_authenticated(client: GSIEClient) -> None:
    respx.post(f"{API}/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "access-abc",
                "refresh_token": "refresh-xyz",
                "token_type": "Bearer",
                "expires_in": 900,
            },
        )
    )
    route = respx.get(f"{API}/diagnostic/status").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    await client.login("admin", "secret")
    await client.diagnostic.status()
    assert route.calls.last.request.headers["Authorization"] == "Bearer access-abc"


@respx.mock
async def test_request_should_refresh_and_retry_when_401(client: GSIEClient) -> None:
    # login initial
    respx.post(f"{API}/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "expired",
                "refresh_token": "refresh-1",
                "token_type": "Bearer",
                "expires_in": 900,
            },
        )
    )
    # refresh retourne un nouveau token
    respx.post(f"{API}/auth/refresh").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "fresh",
                "refresh_token": "refresh-2",
                "token_type": "Bearer",
                "expires_in": 900,
            },
        )
    )
    # 1er appel 401 (token expiré), 2e appel 200 (après refresh)
    route = respx.get(f"{API}/diagnostic/status").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "expired"}),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )
    await client.login("admin", "secret")
    result = await client.diagnostic.status()
    assert result == {"status": "ok"}
    assert route.call_count == 2


@respx.mock
async def test_request_should_raise_token_refresh_error_when_refresh_fails(
    client: GSIEClient,
) -> None:
    respx.post(f"{API}/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "expired",
                "refresh_token": "refresh-1",
                "token_type": "Bearer",
                "expires_in": 900,
            },
        )
    )
    respx.post(f"{API}/auth/refresh").mock(return_value=httpx.Response(401))
    respx.get(f"{API}/diagnostic/status").mock(return_value=httpx.Response(401))
    await client.login("admin", "secret")
    with pytest.raises(TokenRefreshError):
        await client.diagnostic.status()


@respx.mock
async def test_health_should_return_status_when_healthy(client: GSIEClient) -> None:
    respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "healthy"})
    )
    assert await client.health() == {"status": "healthy"}


@respx.mock
async def test_api_error_should_be_raised_when_server_returns_500(client: GSIEClient) -> None:
    respx.get(f"{BASE_URL}/health").mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(APIError) as exc:
        await client.health()
    assert exc.value.status_code == 500
