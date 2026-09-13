from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from socket import getaddrinfo
from typing import Protocol, runtime_checkable
from urllib.parse import urlencode, urlsplit

import httpx

from stock_platform.infrastructure.network.endpoint_policy import (
    EndpointConfig,
    EndpointPolicyError,
    public_address,
    validate_url,
)


@runtime_checkable
class Transport(Protocol):
    """A transport port that never adds its own automatic redirects."""

    async def handle_request(self, request: httpx.Request) -> httpx.Response: ...


@runtime_checkable
class Resolver(Protocol):
    """DNS lookup port, normally socket.getaddrinfo."""

    def __call__(
        self,
        host: str,
        service: int | None = None,
        family: int = 0,
        type: int = 0,
    ) -> Sequence[tuple[int, int, int, str, tuple[str, int]]]: ...


@runtime_checkable
class CredentialResolver(Protocol):
    """The only Keychain lookup invoked by the credential gateway."""

    def credential(self, provider: str, reference: str) -> bytes | None: ...


@dataclass(frozen=True, slots=True)
class NetworkGatewayRequest:
    """One request against a user-approved provider endpoint."""

    provider: str
    method: str
    url: str
    category: str = "provider_request"
    credential: bytes | None = None
    credential_reference: str = "default"
    query: Mapping[str, str] | None = None
    headers: Mapping[str, str] | None = None
    body: bytes | None = None
    correlation_id: str | None = None
    follow_redirects: bool = False


@dataclass(frozen=True, slots=True)
class GatewayResponse:
    """A transport response without any response body mutation."""

    status_code: int
    content: bytes
    headers: Mapping[str, str]
    correlation_id: str | None = None
    redirect_url: str | None = None


@dataclass(frozen=True, slots=True)
class GatewayFollowedRedirect:
    """The final response after all internal redirect hops."""

    status_code: int
    content: bytes
    headers: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class GatewayBlockedTarget:
    """Safe blocked-target disclosure without requests or credentials."""

    provider: str
    endpoint: str
    reason: str
    category: str = "provider_request"
    correlation_id: str | None = None


class NetworkGatewayError(Exception):
    """A blocked gateway request carrying only safe details."""

    def __init__(self, blocked: GatewayBlockedTarget) -> None:
        self.blocked = blocked
        super().__init__(blocked.reason)


class CredentialUnavailableError(Exception):
    """Raised before any request when a required secret cannot be read."""


class CredentialGateway:
    """Resolve a secret only after policy validation and never sign blocked calls."""

    def __init__(self, gateway: NetworkGateway, credentials: CredentialResolver) -> None:
        self._gateway = gateway
        self._credentials = credentials

    async def request(self, request: NetworkGatewayRequest) -> GatewayResponse:
        try:
            validate_url(self._gateway.endpoints[request.provider], request.url)
        except (KeyError, EndpointPolicyError) as error:
            raise self._blocked(request, str(error)) from error
        credential = self._credentials.credential(
            request.provider, request.credential_reference
        )
        if credential is None:
            raise self._gateway._blocked(
                request, "credential unavailable for provider"
            )
        return await self._gateway.request(
            replace(request, credential=credential)
        )

    @staticmethod
    def _blocked(
        request: NetworkGatewayRequest, reason: str
    ) -> NetworkGatewayError:
        return NetworkGatewayError(
            GatewayBlockedTarget(
                provider=request.provider,
                endpoint=request.url,
                reason=reason,
                category=request.category,
                correlation_id=request.correlation_id,
            )
        )


class _HTTPXTransport:
    """Default transport with automatic redirects explicitly disabled."""

    async def handle_request(self, request: httpx.Request) -> httpx.Response:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(20.0, connect=10.0),
        ) as client:
            return await client.request(
                request.method,
                str(request.url),
                headers=request.headers,
                content=request.content,
            )


class NetworkGateway:
    """Validate every hop, then transmit only to the approved provider endpoint."""

    def __init__(
        self,
        endpoints: Mapping[str, EndpointConfig],
        *,
        transport: Transport | None = None,
        resolver: Resolver | None = None,
    ) -> None:
        self.endpoints = dict(endpoints)
        self._transport = transport
        self._resolver = resolver or getaddrinfo
        self.attempts: tuple[str, ...] = ()
        self.is_running = False

    async def request(self, request: NetworkGatewayRequest) -> GatewayResponse:
        endpoint = self._validated_endpoint(request)
        current_url = self._canonicalized_url(request)
        current_url = self._validated_redirect(request, endpoint, current_url)
        response = await self._authorized_send(request, current_url)

        redirect_url = response.headers.get("location")
        while response.status_code in {301, 302, 303, 307, 308} and redirect_url:
            if not request.follow_redirects:
                return self._response(response, request, redirect_url=redirect_url)
            current_url = self._validated_redirect(
                request, endpoint, redirect_url
            )
            response = await self._authorized_send(
                request,
                current_url,
                follow=True,
            )
            redirect_url = response.headers.get("location")
        return self._response(response, request)

    def _validated_endpoint(
        self, request: NetworkGatewayRequest
    ) -> EndpointConfig:
        try:
            endpoint = self.endpoints[request.provider]
            validate_url(endpoint, request.url)
            self._assert_approved_dns(endpoint.host)
        except (KeyError, EndpointPolicyError) as error:
            raise self._blocked(
                request,
                (
                    "provider endpoint is not configured"
                    if isinstance(error, KeyError)
                    else str(error)
                ),
            ) from error
        return endpoint

    @staticmethod
    def _validated_redirect(
        request: NetworkGatewayRequest,
        endpoint: EndpointConfig,
        target_url: str,
    ) -> str:
        try:
            validate_url(endpoint, target_url)
            return target_url
        except EndpointPolicyError as error:
            raise NetworkGateway._blocked(request, str(error)) from error

    async def _authorized_send(
        self,
        request: NetworkGatewayRequest,
        url: str,
        *,
        follow: bool = False,
    ) -> httpx.Response:
        headers = dict(self._safe_headers(request.headers or {}))
        if request.credential is not None and not follow:
            headers["authorization"] = f"Bearer {request.credential.decode('ascii')}"
        method = request.method if not follow else "GET"
        content = None if follow else request.body
        return await self._send(url, method, headers, content)

    @staticmethod
    def _safe_headers(headers: Mapping[str, str]) -> Mapping[str, str]:
        return {
            name: value
            for name, value in headers.items()
            if name.lower() != "authorization"
        }

    @staticmethod
    def _canonicalized_url(request: NetworkGatewayRequest) -> str:
        if request.query:
            separator = "&" if "?" in request.url else "?"
            return f"{request.url}{separator}{urlencode(request.query)}"
        return request.url

    def _assert_approved_dns(self, host: str) -> None:
        addresses = self._resolver(host, 443)
        for family, _, _, _, address in addresses:
            if family in {2, 10} and public_address(str(address[0])):
                return
        raise EndpointPolicyError("provider host has no resolvable address")

    async def _send(
        self,
        url: str,
        method: str,
        headers: Mapping[str, str],
        content: bytes | None,
    ) -> httpx.Response:
        transport = self._transport or _HTTPXTransport()
        request = httpx.Request(method, url, headers=headers, content=content)
        self.attempts = (*self.attempts, str(request.url))
        return await transport.handle_request(request)

    @staticmethod
    def _host(value: str) -> str:
        return urlsplit(value).hostname or ""

    @staticmethod
    def _response(
        response: httpx.Response,
        request: NetworkGatewayRequest,
        *,
        redirect_url: str | None = None,
    ) -> GatewayResponse:
        return GatewayResponse(
            status_code=response.status_code,
            content=response.content,
            headers=dict(response.headers),
            correlation_id=request.correlation_id,
            redirect_url=redirect_url,
        )

    @staticmethod
    def _blocked(
        request: NetworkGatewayRequest, reason: str
    ) -> NetworkGatewayError:
        return NetworkGatewayError(
            GatewayBlockedTarget(
                provider=request.provider,
                endpoint=request.url,
                reason=reason,
                category=request.category,
                correlation_id=request.correlation_id,
            )
        )
