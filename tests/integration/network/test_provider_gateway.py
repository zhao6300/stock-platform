from __future__ import annotations

import asyncio

import httpx

from stock_platform.infrastructure.network.endpoint_policy import EndpointConfig
from stock_platform.infrastructure.network.gateway import (
    NetworkGateway,
    NetworkGatewayRequest,
)


class FakeResolver:
    def __call__(self, host: str, service: int | None = None, family: int = 0, type: int = 0):
        if host != "approved.example.test":
            raise OSError("resolution blocked in local tests")
        return [(2, 1, 6, "", ("93.184.216.34", service or 443))]


class RedirectTransport:
    def __init__(self) -> None:
        self.urls: tuple[str, ...] = ()

    async def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.urls = (*self.urls, str(request.url))
        if self.urls == ("https://approved.example.test/api/start",):
            return httpx.Response(
                302, headers={"location": "https://approved.example.test/api/finish"}
            )
        return httpx.Response(200, content=b"finished")


def test_provider_gateway_signature_and_redirect_chain() -> None:
    transport = RedirectTransport()
    gateway = NetworkGateway(
        endpoints={
            "reference": EndpointConfig(
                host="approved.example.test",
                port=443,
                allowed_base_paths=("/api",),
            )
        },
        transport=transport,
        resolver=FakeResolver(),
    )

    response = asyncio.run(
        gateway.request(
            NetworkGatewayRequest(
                provider="reference",
                method="GET",
                url="https://approved.example.test/api/start",
                credential=b"token",
                correlation_id="gateway-correlation",
                follow_redirects=True,
            )
        )
    )

    assert response.status_code == 200  # noqa: PLR2004
    assert response.content == b"finished"
    assert response.correlation_id == "gateway-correlation"
    assert transport.urls == (
        "https://approved.example.test/api/start",
        "https://approved.example.test/api/finish",
    )
