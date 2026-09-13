from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from stock_platform.domain.provenance import ProviderProvenance

type ProviderCategory = str

_PROVIDER_IDENTIFIER_LIMIT = 255


@dataclass(frozen=True, slots=True)
class AdapterContract:
    """The single, versioned contract every provider adapter must implement."""

    version: str
    auth_schema: tuple[str, ...]
    capabilities: tuple[str, ...]
    fetch: tuple[str, ...]
    normalize: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    provider: str
    category: ProviderCategory


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    markets: tuple[str, ...]
    instrument_types: tuple[str, ...]
    fields: tuple[str, ...]
    date_ranges: tuple[str, ...]
    request_limits: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderEnvelope:
    provider: str
    provider_identifiers: tuple[str, ...]
    source_version: str | None
    correlation_id: str | None
    payload: bytes
    retrieved_at: datetime

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("provider must not be blank")
        if not self.provider_identifiers:
            raise ValueError("provider_identifiers must not be empty")
        if any(
            not identifier or len(identifier) > _PROVIDER_IDENTIFIER_LIMIT
            for identifier in self.provider_identifiers
        ):
            raise ValueError("provider identifiers must contain 1 to 255 characters")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        if self.payload == b"":
            raise ValueError("payload must not be empty")

    def provenance(self) -> ProviderProvenance:
        return ProviderProvenance(
            provider=self.provider,
            provider_identifiers=self.provider_identifiers,
            source_version=self.source_version,
            correlation_id=self.correlation_id,
            retrieved_at=self.retrieved_at,
        )

    def to_resp(self, *, publish: bool = False) -> ProviderProvenance | Mapping[str, object]:
        provenance = self.provenance()
        if publish:
            return provenance
        return {
            "provider": provenance.provider,
            "provider_identifiers": provenance.provider_identifiers,
            "source_version": provenance.source_version,
            "correlation_id": provenance.correlation_id,
            "retrieved_at": provenance.retrieved_at,
            "payload": self.payload,
        }


class ProviderAdapter(Protocol):
    name: str
    contract_version: str

    def auth_schema(self) -> Mapping[str, object]: ...

    async def capabilities(self) -> ProviderCapabilities: ...

    async def fetch(self, request: ProviderRequest) -> AsyncIterator[ProviderEnvelope]: ...

    def normalize(self, envelope: ProviderEnvelope) -> Mapping[str, object]: ...
