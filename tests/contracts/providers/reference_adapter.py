from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import UTC, datetime

from stock_platform.providers.capabilities import CapabilityValue
from stock_platform.providers.contract import (
    AdapterContract,
    ProviderCapabilities,
    ProviderEnvelope,
    ProviderRequest,
)

_RETRIEVED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class ReferenceProviderAdapter:
    """A fake provider adapter used to exercise the public contract."""

    name = "reference"
    contract_version = "1.0"

    @staticmethod
    def contract() -> AdapterContract:
        return AdapterContract(
            version="1.0",
            auth_schema=("bearer",),
            capabilities=("daily_bar", "fund_nav"),
            fetch=("daily_bar", "fund_nav"),
            normalize=("daily_bar", "fund_nav"),
        )

    @staticmethod
    def auth_schema() -> Mapping[str, object]:
        return {"type": "bearer", "reference": "default"}

    @staticmethod
    def capabilities() -> ProviderCapabilities:
        return ProviderCapabilities(
            markets=("a_share",),
            instrument_types=("stock",),
            fields=("open", "close"),
            date_ranges=("daily",),
            request_limits=("daily",),
        )

    @staticmethod
    def fetch(provider_request: ProviderRequest) -> Iterator[ProviderEnvelope]:
        return iter(
            [
                ProviderEnvelope(
                    provider=provider_request.provider,
                    provider_identifiers=("reference-id",),
                    source_version="reference-source",
                    correlation_id="reference-correlation",
                    payload=b"payload",
                    retrieved_at=_RETRIEVED_AT,
                )
            ]
        )

    @staticmethod
    def normalize(envelope: ProviderEnvelope) -> Mapping[str, object]:
        return {"provider_status": envelope.provider, "assets": (envelope.payload,)}

    @staticmethod
    def capability_values() -> tuple[CapabilityValue, ...]:
        return (
            CapabilityValue("daily_bar", "known", True),
            CapabilityValue("fund_nav", "unknown", False),
        )
