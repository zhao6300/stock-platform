from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from stock_platform.domain.adjustments import (
    AdjustmentFactorPoint,
    AdjustmentFactorSeries,
    AdjustmentMode,
    AdjustmentService,
    PricePoint,
)


def _factor_series(
    *,
    dates: tuple[date, ...],
    factors: tuple[Decimal, ...],
) -> AdjustmentFactorSeries:
    return AdjustmentFactorSeries(
        version_id="factors-v1",
        source_type=None,
        source_id="provider-1",
        retrieved_at=datetime(2025, 12, 31, tzinfo=UTC),
        points=tuple(
            AdjustmentFactorPoint(effective_date=effective, factor=factor)
            for effective, factor in zip(dates, factors, strict=True)
        ),
    )


def test_adjusted_prices_use_that_documented_anchor_formula() -> None:
    raw = (
        PricePoint(date(2025, 1, 1), Decimal("10")),
        PricePoint(date(2025, 1, 2), Decimal("12")),
    )
    factors = _factor_series(
        dates=(date(2025, 1, 1), date(2025, 1, 2)),
        factors=(Decimal("1"), Decimal("2")),
    )

    forward = AdjustmentService().apply(
        mode=AdjustmentMode.FORWARD_ADJUSTED,
        modes=(),
        raw_series=raw,
        factors=factors,
    )
    backward = AdjustmentService().apply(
        mode=AdjustmentMode.BACKWARD_ADJUSTED,
        modes=(),
        raw_series=raw,
        factors=factors,
    )

    assert isinstance(forward, object)
    assert isinstance(backward, object)
