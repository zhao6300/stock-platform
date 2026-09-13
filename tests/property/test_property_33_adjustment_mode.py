from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.adjustments import (
    PERMITTED_MODES,
    AdjustmentFactorPoint,
    AdjustmentFactorSeries,
    AdjustmentFactorSource,
    AdjustmentMode,
    AdjustmentService,
    PricePoint,
)
from stock_platform.domain.common import Success


def _factor_series() -> AdjustmentFactorSeries:
    return AdjustmentFactorSeries(
        version_id="factors-v1",
        source_type=AdjustmentFactorSource.PROVIDER,
        source_id="source-1",
        retrieved_at=datetime(2025, 12, 1, tzinfo=UTC),
        points=(AdjustmentFactorPoint(effective_date=date(2025, 1, 1), factor=Decimal(1)),),
    )


@given(mode=st.sampled_from(PERMITTED_MODES))
def test_price_requests_require_one_valid_mode(mode: object) -> None:
    if isinstance(mode, AdjustmentMode) and mode in PERMITTED_MODES:
        result = AdjustmentService().apply(
            mode=mode,
            modes=(),
            raw_series=(PricePoint(date(2025, 1, 1), Decimal(10)),),
            factors=_factor_series(),
        )
        assert isinstance(result, Success)
    else:
        assert mode not in PERMITTED_MODES
