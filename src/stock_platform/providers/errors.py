from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

type ProviderCategory = str


@dataclass(frozen=True, slots=True)
class RateLimitError(Exception):
    """A provider-facing request was rejected for exceeding a request limit."""

    provider: str
    category: ProviderCategory
    retry_eligible: bool
    retry_after_seconds: Decimal | None = None
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderUnavailable(Exception):
    """A configured provider endpoint could not fulfill the request."""

    provider: str
    endpoint_id: str
    correlation_id: str | None = None

    @property
    def category(self) -> str:
        return "PROVIDER_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class EnvelopeValidationError(Exception):
    provider: str
    fields: tuple[str, ...]

    @property
    def category(self) -> str:
        return "VALIDATION"
