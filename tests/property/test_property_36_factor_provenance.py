from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.adjustments import (
    AdjustmentFactorPoint,
    AdjustmentFactorSeries,
    AdjustmentFactorSource,
)


@given(
    source_type=st.sampled_from(tuple(AdjustmentFactorSource)),
    source_id=st.text(min_size=1, max_size=8),
    version_id=st.text(min_size=1, max_size=8),
)
def test_factor_provenance_is_exclusive_and_complete(
    source_type: AdjustmentFactorSource,
    source_id: str,
    version_id: str,
) -> None:
    series = AdjustmentFactorSeries(
        version_id=version_id,
        source_type=source_type,
        source_id=source_id,
        retrieved_at=datetime(2025, 1, 1, tzinfo=UTC),
        points=(AdjustmentFactorPoint(date(2025, 1, 1), Decimal(1)),),
    )

    assert series.source_type == source_type
    assert series.source_id == source_id
    assert series.version_id == version_id
    assert series.validate_source() is True
