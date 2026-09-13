from __future__ import annotations

from datetime import UTC, datetime

import pytest

from stock_platform.providers.contract import ProviderEnvelope
from stock_platform.providers.errors import RateLimitError


def test_provider_envelope_validates_and_carries_provenance() -> None:
    retrieved_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    envelope = ProviderEnvelope(
        provider="provider",
        provider_identifiers=("id",),
        source_version="version",
        correlation_id="correlation",
        payload=b"payload",
        retrieved_at=retrieved_at,
    )

    provenance = envelope.provenance()
    assert provenance.retrieved_at == retrieved_at
    assert envelope.to_resp() == {
        "provider": "provider",
        "provider_identifiers": ("id",),
        "source_version": "version",
        "correlation_id": "correlation",
        "retrieved_at": retrieved_at,
        "payload": b"payload",
    }


@pytest.mark.parametrize("retry_after", [None, 301])
def test_rate_limit_error_contains_safe_required_context(retry_after: int | None) -> None:
    error = RateLimitError(
        provider="provider",
        category="daily_bar",
        retry_eligible=True,
        retry_after_seconds=retry_after,
        correlation_id="correlation-id",
    )

    assert error.provider == "provider"
    assert error.category == "daily_bar"
    assert error.retry_eligible is True
    assert error.retry_after_seconds == retry_after
