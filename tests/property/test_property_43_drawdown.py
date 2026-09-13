from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import assume, given
from hypothesis import strategies as st

from stock_platform.domain.analytics import drawdown
from stock_platform.domain.common import SeriesPoint


@given(
    values=st.lists(
        st.one_of(
            st.none(),
            st.decimals(
                min_value=Decimal("0.01"),
                max_value=Decimal("1e12"),
                allow_nan=False,
            ),
        ),
        min_size=1,
        max_size=40,
    ),
)
def test_drawdown_follows_the_running_maximum(values: list[Decimal | None]) -> None:
    assume(any(value is not None for value in values))
    assume(values[-1] is None or values[-1] != Decimal(0))
    points = [
        SeriesPoint(date(2025, 1, (index % 31) + 1), value)
        for index, value in enumerate(values)
    ]
    result = drawdown(points)

    running: Decimal | None = None
    maximum: Decimal = Decimal(0)
    pointwise = []
    for value in values:
        if value is None:
            pointwise.append(None)
            continue
        running = value if running is None else max(running, value)
        pointwise.append(value / running - 1)
        maximum = min(maximum, pointwise[-1])

    assert result.value == (tuple(pointwise), maximum)
