"""Configured HTTPS endpoint policy checks."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


class EndpointPolicyError(ValueError):
   """Raised when a URL is not within the configured provider endpoint."""


def public_address(host: str) -> str:
    """Return host for DNS resolution; no IP literals are allowed."""
    return host

@dataclass(frozen=True, slots=True)
class EndpointConfig:
    """The user-approved origin and base path boundary."""

    host: str
    port: int | None = None
    allowed_base_paths: tuple[str, ...] = ("/",)

    @property
    def is_https(self) -> bool:
        return self.host.startswith("https://")

    @property
    def origin(self) -> str:
        return self.host


def parse_endpoint(value: str) -> tuple[str, int | None]:
    """Normalize a user-approved HTTPS origin."""
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise EndpointPolicyError("malformed provider endpoint") from error
    if parsed.scheme != "https":
        raise EndpointPolicyError("provider endpoint scheme must be HTTPS")
    if parsed.username or parsed.password:
        raise EndpointPolicyError("provider endpoint userinfo is not allowed")
    if not parsed.hostname:
        raise EndpointPolicyError("provider endpoint host is required")
    return parsed.hostname.lower(), parsed.port


def validate_url(config: EndpointConfig, value: str) -> str:
    """Return the canonical HTTPS URL, or the reason the request was rejected."""
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise EndpointPolicyError("malformed provider URL") from error
    if parsed.scheme != "https":
        raise EndpointPolicyError("request scheme must be HTTPS")
    if parsed.username or parsed.password:
        raise EndpointPolicyError("request userinfo is not allowed")
    if not parsed.hostname or parsed.hostname.lower() != config.host:
        raise EndpointPolicyError("blocked request host")
    if parsed.port is not None and parsed.port != config.port:
        raise EndpointPolicyError("blocked request port")
    if not any(parsed.path.startswith(base_path) for base_path in config.allowed_base_paths):
        raise EndpointPolicyError("blocked request path")
    return ""
