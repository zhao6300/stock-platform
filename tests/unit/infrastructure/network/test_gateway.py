from __future__ import annotations

import asyncio

import httpx
import pytest

from stock_platform.infrastructure.network.endpoint_policy import EndpointConfig
from stock_platform.infrastructure.network.gateway import (
    NetworkGateway,
    NetworkGatewayError,
    NetworkGatewayRequest,
)


class FakeResolver:
    def __call__(self, host: str, service: int | None = None, family: int = 0, type: int = 0):
        if host != "approved.example.test":
            raise OSError("resolution blocked in local tests")
        return [(2, 1, 6, "", ("93.184.216.34", service or 443))]


class ScriptedTransport:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.urls: tuple[str, ...] = ()

    async def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.urls = (*self.urls, str(request.url))
        return self.responses.pop(0)


def test_gateway_does_not_follow_when_redirects_are_opt_in() -> None:
    transport = ScriptedTransport(
        [
            httpx.Response(
                302,
                headers={"location": "https://approved.example.test/redirected"},
                content=b"redirect response",
            )
        ]
    )
    gateway = NetworkGateway(
        endpoints={"alpha": EndpointConfig(host="approved.example.test", port=443)},
        transport=transport,
        resolver=FakeResolver(),
    )

    response = asyncio.run(
        gateway.request(
            NetworkGatewayRequest(
                provider="alpha",
                method="GET",
                url="https://approved.example.test/start",
            )
        )
    )

    assert response.status_code == httpx.codes.FOUND
    assert response.redirect_url == "https://approved.example.test/redirected"
    assert transport.urls == ("https://approved.example.test/start",)


def test_gateway_follows_only_within_configured_endpoint() -> None:
    transport = ScriptedTransport(
        [
            httpx.Response(302, headers={"location": "https://approved.example.test/next"}),
            httpx.Response(200, content=b"final response"),
        ]
    )
    gateway = NetworkGateway(
        endpoints={"alpha": EndpointConfig(host="approved.example.test", port=443)},
        transport=transport,
        resolver=FakeResolver(),
    )

    response = asyncio.run(
        gateway.request(
            NetworkGatewayRequest(
                provider="alpha",
                method="GET",
                url="https://approved.example.test/start",
                follow_redirects=True,
            )
        )
    )

    assert response.status_code == httpx.codes.OK
    assert response.content == b"final response"
    assert transport.urls == (
        "https://approved.example.test/start",
        "https://approved.example.test/next",
    )


def test_gateway_blocks_cross_origin_redirect_before_hop() -> None:
    transport = ScriptedTransport(
        [
            httpx.Response(
                302,
                headers={"location": "https://blocked.example.test/target"},
            )
        ]
    )
    gateway = NetworkGateway(
        endpoints={"alpha": EndpointConfig(host="approved.example.test", port=443)},
        transport=transport,
        resolver=FakeResolver(),
    )

    with pytest.raises(NetworkGatewayError) as raised:
        asyncio.run(
            gateway.request(
                NetworkGatewayRequest(
                    provider="alpha",
                    method="GET",
                    url="https://approved.example.test/start",
                    follow_redirects=True,
                )
            )
        )

    assert raised.value.blocked.endpoint == "https://approved.example.test/start"
    assert transport.urls == ("https://approved.example.test/start",)
