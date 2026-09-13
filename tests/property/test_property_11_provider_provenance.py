from __future__ import annotations

from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.providers.contract import ProviderEnvelope


@given(
    provider=st.text(min_size=1, max_size=64),
    provider_identifier=st.text(min_size=1, max_size=255),
    source_version=st.one_of(st.none(), st.text(min_size=1, max_size=64)),
    correlation_id=st.one_of(st.none(), st.text(min_size=1, max_size=64)),
    payload=st.binary(min_size=1, max_size=255),
)
def test_provider_provenance_survives_normalization(
    provider: str,
    provider_identifier: str,
    source_version: str | None,
    correlation_id: str | None,
    payload: bytes,
) -> None:
    envelope = ProviderEnvelope(
        provider=provider,
        provider_identifiers=(provider_identifier,),
        source_version=source_version,
        correlation_id=correlation_id,
    retrieved_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        payload=payload,
    )

    provenance = envelope.provenance()
    assert provenance.provider == provider
    assert provenance.provider_identifiers == (provider_identifier,)
    assert provenance.source_version == source_version
    assert provenance.correlation_id == correlation_id
    assert provenance.retrieved_at == datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
