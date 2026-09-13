from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.adjustments import fund_nav_fallback
from stock_platform.domain.common import Success
from stock_platform.domain.ingestion import FundNav


@given(
    unit_nav=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e12")),
    cumulative_nav=st.one_of(
        st.none(),
        st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e12")),
    ),
)
def test_cumulative_nav_is_provider_only_with_explicit_fallback(
    unit_nav: Decimal,
    cumulative_nav: Decimal | None,
) -> None:
    observation = FundNav(
        observation_date=date(2025, 1, 1),
        unit_nav=unit_nav,
        cumulative_nav=cumulative_nav,
        currency="CNY",
    )

    result = fund_nav_fallback(observation)

    assert isinstance(result, Success)
    assert result.value.unit_nav == unit_nav
    assert result.value.cumulative_nav == cumulative_nav
    assert result.value.cumulative_nav_available is (cumulative_nav is not None)
    assert result.value.cumulative_nav_status == (
        "AVAILABLE" if cumulative_nav is not None else "UNAVAILABLE"
    )
