from __future__ import annotations

import asyncio

import httpx
from hypothesis import given
from hypothesis import strategies as st

from stock_platform.infrastructure.network.endpoint_policy import EndpointConfig
from stock_platform.infrastructure.network.gateway import (
    NetworkGateway,
    NetworkGatewayError,
    NetworkGatewayRequest,
)


class RecordingTransport:
    def __init__(self) -> None:
        self.urls: tuple[str, ...] = ()

    async def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.urls = (*self.urls, str(request.url))
        return httpx.Response(200, content=b"allowed")


class FakeResolver:
    def __call__(self, host: str, service: int | None = None, family: int = 0, type: int = 0):
        if host != "approved.example.test":
            raise OSError("resolution blocked in local tests")
        return [(2, 1, 6, "", ("93.184.216.34", service or 443))]


allowed_urls = st.just("https://approved.example.test/api/data")
blocked_urls = st.one_of(
    st.just("http://approved.example.test/api/data"),
    st.just("https://blocked.example.test/api/data"),
    st.just("https://approved.example.test/outside-base-path"),
)
redirect_destinations = st.one_of(
    st.just("https://approved.example.test/inside"),
    st.just("https://blocked.example.test/outside"),
)


@given(url=allowed_urls, redirect_url=redirect_destinations)
def test_gateway_transmits_only_within_configured_endpoints(url: str, redirect_url: str) -> None:
    transport = RecordingTransport()
    gateway = NetworkGateway(
        endpoints={
            "alpha": EndpointConfig(
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
                provider="alpha",
                method="GET",
                url=url,
                follow_redirects=True,
            )
        )
    )

    assert response.status_code == httpx.codes.OK
    assert all(item.startswith("https://approved.example.test/") for item in transport.urls)


@given(url=blocked_urls)
def test_gateway_preserves_state_when_targets_are_blocked(url: str) -> None:
    transport = RecordingTransport()
    gateway = NetworkGateway(
        endpoints={
            "alpha": EndpointConfig(
                host="approved.example.test",
                port=443,
                allowed_base_paths=("/api",),
            )
        },
        transport=transport,
        resolver=FakeResolver(),
    )

    try:
        asyncio.run(
            gateway.request(
                NetworkGatewayRequest(
                    provider="alpha",
                    method="GET",
                    url=url,
                )
            )
        )
    except NetworkGatewayError as error:
        reason = error.blocked.reason
    else:
        raise AssertionError("expected the target to be blocked")

    assert reason
    assert transport.urls == ()
