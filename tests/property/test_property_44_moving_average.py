from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.analytics import moving_average
from stock_platform.domain.common import SeriesPoint


@given(
    values=st.lists(
        st.one_of(
            st.none(),
            st.decimals(min_value=Decimal("-1e12"), max_value=Decimal("1e12"), allow_nan=False),
        ),
        min_size=1,
        max_size=30,
    ),
    window=st.integers(min_value=1, max_value=10000),
)
def test_moving_average_uses_exactly_w_non_missing_values(
    values: list[Decimal | None],
    window: int,
) -> None:
    points = [SeriesPoint(date(2025, 1, index + 1), value) for index, value in enumerate(values)]
    result = moving_average(points, window)

    seen: list[Decimal] = []
    expected: list[Decimal | None] = []
    for value in values:
        if value is not None:
            seen.append(value)
        expected.append(
            None
            if value is None or len(seen) < window
            else sum(seen[-window:], Decimal(0)) / window
        )

    assert result.value == tuple(expected)
