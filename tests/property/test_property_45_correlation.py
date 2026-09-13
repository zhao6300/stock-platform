from __future__ import annotations

from datetime import date
from decimal import Decimal, getcontext

from hypothesis import assume, given
from hypothesis import strategies as st

from stock_platform.domain.analytics import UndefinedCorrelation, correlation
from stock_platform.domain.common import Failure, SeriesPoint


@given(
    left=st.lists(
        st.decimals(min_value=Decimal("1e-4"), max_value=Decimal("1e12"), allow_nan=False),
        min_size=3,
        max_size=8,
    ),
    right=st.lists(
        st.one_of(
            st.none(),
            st.decimals(min_value=Decimal("1e-4"), max_value=Decimal("1e12"), allow_nan=False),
        ),
        min_size=3,
        max_size=8,
    ),
)
def test_correlation_uses_aligned_shared_dates(
    left: list[Decimal], right: list[Decimal | None]
) -> None:
    dates = [date(2025, 1, index + 1) for index in range(min(len(left), len(right)))]
    ordered_right = [
        SeriesPoint(value_date, value) for value_date, value in zip(dates, right, strict=False)
    ]
    aligned = [
        (left[index], ordered_right[index].value)
        for index in range(len(dates))
        if ordered_right[index].value is not None
    ]
    if len(aligned) <= 1:
        return
    left_mean = sum(aligned_left for aligned_left, _ in aligned) / len(aligned)
    left_variance = sum((aligned_left - left_mean) ** 2 for aligned_left, _ in aligned)
    right_mean = sum(aligned_right for _, aligned_right in aligned) / len(aligned)
    right_variance = sum((aligned_right - right_mean) ** 2 for _, aligned_right in aligned)
    assume(left_variance != 0 and right_variance != 0)
    expected = sum(
        (aligned_left - left_mean) * (aligned_right - right_mean)
        for aligned_left, aligned_right in aligned
    ) / (left_variance * right_variance).sqrt(getcontext())
    result = correlation(
        [SeriesPoint(value_date, value) for value_date, value in zip(dates, left, strict=False)],
        ordered_right,
    )

    assert result.value == expected


def test_correlation_reports_each_zero_variance_side() -> None:
    dates = (date(2025, 1, 1), date(2025, 1, 2))
    constant_left = [SeriesPoint(dates[0], Decimal("2")), SeriesPoint(dates[1], Decimal("2"))]
    variable_right = [SeriesPoint(dates[0], Decimal("1")), SeriesPoint(dates[1], Decimal("3"))]
    variable_left = [SeriesPoint(dates[0], Decimal("1")), SeriesPoint(dates[1], Decimal("4"))]
    constant_right = [SeriesPoint(dates[0], Decimal("5")), SeriesPoint(dates[1], Decimal("5"))]

    assert correlation(constant_left, variable_right) == Failure(UndefinedCorrelation(("left",)))
    assert correlation(variable_left, constant_right) == Failure(UndefinedCorrelation(("right",)))
