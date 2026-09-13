from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.analytics import InsufficientData, ReturnPoint, drawdown, returns
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.fundamentals import SeriesPoint

_MINIMUM_OBSERVATIONS = 2


def _points(
    values: Sequence[Decimal | None],
    *,
    start: int | None = None,
) -> list[SeriesPoint]:
    base = start or 2025
    days = sorted({date(base, 1, 1) + timedelta(days=lidex) for lidex, _ in enumerate(values)})[
        : len(values)
    ]
    return [SeriesPoint(value_date, value) for value_date, value in zip(days, values, strict=False)]


@given(
    values=st.lists(
        st.one_of(
            st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.00"), places=6),
            st.none(),
        ),
        min_size=2,
        max_size=34,
    )
)
def test_periodic_returns_follow_consecutive_non_missing_values(
    values: list[Decimal | None],
) -> None:
    series = _points(values)
    present = [point for point in series if point.value is not None]
    expected = (
        Success(
            tuple(
                ReturnPoint(date=second.date, value=second.value / first.value - 1)
                for first, second in pairwise(present)
            )
        )
        if len(present) >= _MINIMUM_OBSERVATIONS
        else Failure(InsufficientData(required=2, available=len(present)))
    )

    result = returns(series)
    assert result == expected


def test_drawdown_returns_expected_values() -> None:
    series = [
        SeriesPoint(date(2025, 1, 1), value=Decimal("1")),
        SeriesPoint(date(2025, 1, 2), value=Decimal("2")),
    ]
    assert drawdown(series).value == ((Decimal("0"), Decimal("0")), Decimal("0"))
