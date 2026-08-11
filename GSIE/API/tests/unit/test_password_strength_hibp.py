"""Couverture du client HIBP k-anonymity (HttpxHibpClient)."""

from __future__ import annotations

import httpx
import respx
from httpx import Response

from gsie_api.auth.password_strength import HttpxHibpClient

_RANGE_URL = "https://api.pwnedpasswords.com/range/ABCDE"


@respx.mock
async def should_parse_hibp_suffix_counts() -> None:
    respx.get(_RANGE_URL).mock(
        return_value=Response(
            200,
            text=(
                "0018A45C4D1DEF81644B54AB7F969B88D65:1\r\n"
                "00D4F6E8FA6EECAD2A3AA415EEC418D38EC:2\r\n"
                "malformed-line-without-colon\r\n"
                "SUFFIXWITHNONNUMERICCOUNT:not-a-number\r\n"
            ),
        )
    )

    client = HttpxHibpClient()
    result = await client.fetch_suffixes("ABCDE")

    assert result["0018A45C4D1DEF81644B54AB7F969B88D65"] == 1
    assert result["00D4F6E8FA6EECAD2A3AA415EEC418D38EC"] == 2
    assert "malformed-line-without-colon" not in result
    assert "SUFFIXWITHNONNUMERICCOUNT" not in result


@respx.mock
async def should_raise_on_hibp_http_error() -> None:
    respx.get(_RANGE_URL).mock(return_value=Response(503))

    client = HttpxHibpClient()
    try:
        await client.fetch_suffixes("ABCDE")
    except httpx.HTTPStatusError:
        pass
    else:
        raise AssertionError("attendait une httpx.HTTPStatusError")
