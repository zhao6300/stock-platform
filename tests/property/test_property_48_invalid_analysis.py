from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.analytics import InvalidWindow, moving_average
from stock_platform.domain.common import Failure, SeriesPoint


@given(window=st.integers(max_value=0))
def test_invalid_analysis_inputs_preserve_prior_result(window: int) -> None:
    point = SeriesPoint(date(2026, 1, 1), Decimal("5"))

    result = moving_average([point], window)

    assert isinstance(result, Failure)
    assert result.error == InvalidWindow(minimum=1, maximum=10000)
    assert point.date == date(2026, 1, 1)
    assert point.value == Decimal("5")
