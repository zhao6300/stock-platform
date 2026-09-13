from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from stock_platform.domain.adjustments import (
    AdjustmentFactorPoint,
    AdjustmentFactorSeries,
    AdjustmentFactorSource,
    AdjustmentMode,
    AdjustmentService,
    PricePoint,
)


@settings(max_examples=100)
@given(raw_price=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e12")))
def test_unadjusted_prices_are_identical(raw_price: Decimal) -> None:
    raw = (PricePoint(date(2025, 1, 1), raw_price),)
    factors = AdjustmentFactorSeries(
        version_id="factors-v1",
        source_type=AdjustmentFactorSource.PROVIDER,
        source_id="provider-1",
        retrieved_at=datetime(2025, 12, 1, tzinfo=UTC),
        points=(AdjustmentFactorPoint(effective_date=date(2025, 1, 1), factor=Decimal(2)),),
    )
    result = AdjustmentService().apply(
        mode=AdjustmentMode.UNADJUSTED,
        modes=(),
        raw_series=raw,
        factors=factors,
    )

    adjusted = result.value
    assert adjusted.mode == AdjustmentMode.UNADJUSTED
    assert adjusted.values == raw
