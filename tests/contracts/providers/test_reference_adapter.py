from __future__ import annotations

from tests.contracts.providers.reference_adapter import ReferenceProviderAdapter

from stock_platform.providers.capabilities import CapabilityProbe
from stock_platform.providers.contract import ProviderRequest
from stock_platform.providers.errors import ProviderUnavailable, RateLimitError


def test_reference_adapter_implements_contract_and_capabilities() -> None:
    adapter = ReferenceProviderAdapter()
    contract = adapter.contract()

    assert adapter.name == "reference"
    assert adapter.contract_version == contract.version
    assert adapter.auth_schema()["type"] == "bearer"
    assert adapter.capabilities().markets == ("a_share",)
    assert adapter.capability_values()[0].reported is True


def test_reference_adapter_preserves_provenance_and_normalization() -> None:
    adapter = ReferenceProviderAdapter()
    envelope = next(
        iter(adapter.fetch(ProviderRequest(provider="reference", category="daily_bar")))
    )

    assert envelope.provider == "reference"
    assert envelope.provider_identifiers == ("reference-id",)
    assert envelope.correlation_id == "reference-correlation"
    assert adapter.normalize(envelope)["provider_status"] == "reference"


def test_reference_adapter_reports_categorized_failures() -> None:
    rate_limit = RateLimitError(
        provider="reference",
        category="daily_bar",
        retry_eligible=True,
        correlation_id="reference-correlation",
    )
    unavailable = ProviderUnavailable(
        provider="reference",
        endpoint_id="reference",
        correlation_id="reference-correlation",
    )
    probe = CapabilityProbe(outcome="failure", unsupported=())

    assert rate_limit.retry_eligible is True
    assert unavailable.category == "PROVIDER_UNAVAILABLE"
    assert probe.outcome == "failure"
