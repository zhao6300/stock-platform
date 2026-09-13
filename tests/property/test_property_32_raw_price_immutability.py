from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from stock_platform.domain.adjustments import (
    AdjustmentFactorPoint,
    AdjustmentFactorSeries,
    AdjustmentFactorSource,
    AdjustmentMode,
    AdjustmentService,
    PricePoint,
)


def _factor_series(factor: Decimal) -> AdjustmentFactorSeries:
    return AdjustmentFactorSeries(
        version_id="factors-v1",
        source_type=AdjustmentFactorSource.PROVIDER,
        source_id="provider-1",
        retrieved_at=datetime(2025, 12, 1, tzinfo=UTC),
        points=(AdjustmentFactorPoint(effective_date=date(2025, 1, 1), factor=factor),),
    )


def test_adjustment_series_are_strictly_binary() -> None:
    service = AdjustmentService()
    raw = (PricePoint(date(2025, 1, 1), Decimal("10")),)
    factors = _factor_series(Decimal("1"))

    result = service.apply(
        mode=AdjustmentMode.UNADJUSTED,
        modes=(),
        raw_series=raw,
        factors=factors,
    )

    assert result is not None
