from __future__ import annotations

import asyncio
from dataclasses import dataclass

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.infrastructure.network.endpoint_policy import EndpointConfig
from stock_platform.infrastructure.network.gateway import (
    CredentialGateway,
    NetworkGateway,
    NetworkGatewayError,
    NetworkGatewayRequest,
)


class FakeResolver:
    def __call__(
        self, host: str, service: int | None = None, family: int = 0, type: int = 0
    ):
        if host != "approved.example.test":
            raise OSError("resolution blocked in local tests")
        return [(2, 1, 6, "", ("93.184.216.34", service or 443))]


@dataclass(frozen=True)
class FakeCredentials:
    missing: bool

    def credential(self, provider: str, reference: str) -> bytes | None:
        return None if self.missing else b"secret-token"


credential_names = st.text(
    alphabet=st.characters(categories=("L", "N"), max_codepoint=0x17F),
    min_size=1,
    max_size=24,
)


@given(provider=credential_names, reference=credential_names)
def test_absent_credential_blocks_the_transport(provider: str, reference: str) -> None:
    gateway = NetworkGateway(
        endpoints={provider: EndpointConfig(host="approved.example.test", port=443)},
        resolver=FakeResolver(),
    )
    credential_gateway = CredentialGateway(gateway, FakeCredentials(missing=True))
    request = NetworkGatewayRequest(
        provider=provider,
        method="GET",
        url="https://approved.example.test/.health",
        credential=None,
        credential_reference=reference,
    )

    try:
        asyncio.run(credential_gateway.request(request))
    except NetworkGatewayError:
        pass
    else:
        raise AssertionError("expected the credential to block the request")
    assert gateway.attempts == ()
