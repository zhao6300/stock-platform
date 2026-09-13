from __future__ import annotations

from datetime import date
from decimal import Decimal

from stock_platform.domain.analytics import (
    CorrelationResult,
    InsufficientData,
    InvalidWindow,
    MovingAverageResult,
    ReturnPoint,
    UndefinedCorrelation,
    correlation,
    drawdown,
    moving_average,
    returns,
    volatility,
)
from stock_platform.domain.common import Failure, SeriesPoint, Success


def test_returns_are_precise_on_two_values() -> None:
    value = returns(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("1.20")),
            SeriesPoint(date(2025, 1, 2), Decimal("1.44")),
        ],
    )

    return_point = value.value[0]
    first, second = return_point.date, return_point.value
    assert (first, second) == (date(2025, 1, 2), Decimal("0.2"))


def test_results_report_required_and_available_counts() -> None:
    failure = returns((SeriesPoint(date(2025, 1, 1), Decimal(1)),))

    assert failure == Failure(InsufficientData(required=2, available=1))


def test_window_limits_are_reported() -> None:
    failure = moving_average(
        [
            SeriesPoint(date(2025, 1, 1), Decimal(1)),
            SeriesPoint(date(2025, 1, 2), Decimal(2)),
        ],
        10_001,
    )

    assert failure == Failure(InvalidWindow(minimum=1, maximum=10_000))


def test_window_limits_confirm_a_valid_middle_value() -> None:
    result: MovingAverageResult = moving_average(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("1")),
            SeriesPoint(date(2025, 1, 2), Decimal("2")),
            SeriesPoint(date(2025, 1, 3), 3.0),
        ],
        2,
    )

    assert result == Success((None, Decimal("1.5"), Decimal("2.5")))


def test_movavg_menus() -> None:
    result: MovingAverageResult = moving_average(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("1")),
            SeriesPoint(date(2025, 1, 2), Decimal("2")),
            SeriesPoint(date(2025, 1, 3), None),
            SeriesPoint(date(2025, 1, 4), Decimal("3")),
            SeriesPoint(date(2025, 1, 5), Decimal("4")),
        ],
        2,
    )

    assert result.value == (
        None,
        Decimal("1.5"),
        None,
        Decimal("2.5"),
        Decimal("3.5"),
    )


def test_drawdown_is_positive_by_point() -> None:
    result = drawdown(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("100")),
            SeriesPoint(date(2025, 2, 1), Decimal("120")),
        ],
    )
    pointwise, maximum = result.value
    assert pointwise == (Decimal("0"), Decimal("0"))
    assert maximum == Decimal("0")


def test_returns_skip_missing_values_without_extrapolating() -> None:
    result = returns(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("10")),
            SeriesPoint(date(2025, 1, 2), None),
            SeriesPoint(date(2025, 1, 3), Decimal("12")),
            SeriesPoint(date(2025, 1, 4), Decimal("15")),
        ],
    )

    assert result.value == (
        ReturnPoint(date(2025, 1, 3), Decimal("0.2")),
        ReturnPoint(date(2025, 1, 4), Decimal("0.25")),
    )


def test_volatility_uses_sample_deviation_and_sqrt_252() -> None:
    result = volatility(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("0.02")),
            SeriesPoint(date(2025, 1, 2), Decimal("0.04")),
            SeriesPoint(date(2025, 1, 3), Decimal("0.06")),
        ],
    )

    annualized, factor = result.value
    expected = (Decimal("0.02") ** 2).sqrt() * Decimal("252").sqrt()
    assert annualized == expected
    assert factor == Decimal("252")


def test_drawdown_tracks_running_maximum_positive_values() -> None:
    result = drawdown(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("100")),
            SeriesPoint(date(2025, 1, 2), Decimal("80")),
            SeriesPoint(date(2025, 1, 3), Decimal("120")),
            SeriesPoint(date(2025, 1, 4), Decimal("90")),
        ],
    )

    pointwise, maximum = result.value
    assert pointwise == (
        Decimal("0"),
        Decimal("-0.2"),
        Decimal("0"),
        Decimal("-0.25"),
    )
    assert maximum == Decimal("-0.25")


def test_moving_average_uses_exactly_window_values() -> None:
    result: MovingAverageResult = moving_average(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("1")),
            SeriesPoint(date(2025, 1, 2), Decimal("2")),
            SeriesPoint(date(2025, 1, 3), Decimal("3")),
            SeriesPoint(date(2025, 1, 4), Decimal("4")),
        ],
        2,
    )

    assert result.value == (
        None,
        Decimal("1.5"),
        Decimal("2.5"),
        Decimal("3.5"),
    )


def test_correlation_uses_only_aligned_shared_dates() -> None:
    result: CorrelationResult = correlation(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("1")),
            SeriesPoint(date(2025, 1, 2), None),
            SeriesPoint(date(2025, 1, 3), Decimal("2")),
            SeriesPoint(date(2025, 1, 4), Decimal("3")),
        ],
        [
            SeriesPoint(date(2025, 1, 1), Decimal("11")),
            SeriesPoint(date(2025, 1, 2), Decimal("99")),
            SeriesPoint(date(2025, 1, 3), Decimal("12")),
            SeriesPoint(date(2025, 1, 4), Decimal("13")),
        ],
    )

    assert result == Success(Decimal("1"))


def test_correlation_reports_each_zero_variance_side() -> None:
    result: CorrelationResult = correlation(
        [
            SeriesPoint(date(2025, 1, 1), Decimal("1")),
            SeriesPoint(date(2025, 1, 2), Decimal("2")),
        ],
        [
            SeriesPoint(date(2025, 1, 1), Decimal("9")),
            SeriesPoint(date(2025, 1, 2), Decimal("9")),
        ],
    )

    assert result == Failure(UndefinedCorrelation(zero_variance=("right",)))
