from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.providers.errors import RateLimitError


@given(
    provider=st.from_regex(r"\w+", fullmatch=True),
    category=st.from_regex(r"\w+", fullmatch=True),
    retry_eligible=st.booleans(),
    retry_after_seconds=st.one_of(st.none(), st.integers(min_value=0, max_value=3600).map(Decimal)),
    correlation_id=st.one_of(st.none(), st.from_regex(r"\w+", fullmatch=True)),
)
def test_rate_limit_translation_is_complete(
    provider: str,
    category: str,
    retry_eligible: bool,
    retry_after_seconds: Decimal | None,
    correlation_id: str | None,
) -> None:
    translation = RateLimitError(
        provider=provider,
        category=category,
        retry_eligible=retry_eligible,
        retry_after_seconds=retry_after_seconds,
        correlation_id=correlation_id,
    )

    assert translation.provider == provider
    assert translation.category == category
    assert translation.retry_eligible is retry_eligible
    assert translation.retry_after_seconds == retry_after_seconds
    assert translation.correlation_id == correlation_id
