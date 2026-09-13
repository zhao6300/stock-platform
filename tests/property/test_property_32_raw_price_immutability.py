from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.adjustments import PricePoint, RawPriceSeries


@given(
    raw_price=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e12")),
    updated_factor=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e12")),
)
def test_raw_prices_are_immutable(
    raw_price: Decimal,
    updated_factor: Decimal,
) -> None:
    point = RawPriceSeries(
        values=(PricePoint(date(2025, 1, 1), raw_price),),
    )
    stored_raw = point.values[0].raw_price
    assert updated_factor >= Decimal(0)
    assert stored_raw == raw_price
