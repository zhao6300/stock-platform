from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, getcontext
from typing import Literal

from stock_platform.domain.common import (
    Failure,
    Result,
    SeriesPoint,
    Success,
    _mean,
)

type MissingNumeric = Decimal | None
type ZeroVarianceSide = Literal["left", "right"]

__all__ = ()

_MINIMUM_CORRELATION_LENGTH = 2
_MINIMUM_RETURN_LENGTH = 2
_MINIMUM_DRAWDOWN_LENGTH = 1
_ANNUALIZATION_FACTOR = Decimal("252")
_MAXIMUM_MOVING_AVERAGE_WINDOW = 10_000
_MINIMUM_MOVING_AVERAGE_WINDOW = 1


@dataclass(frozen=True, slots=True)
class ReturnPoint:
    """Return from the prior non-missing observation, labeled by its date."""

    date: date
    value: Decimal


@dataclass(frozen=True, slots=True)
class InsufficientData:
    required: int
    available: int


@dataclass(frozen=True, slots=True)
class PassiveSeries:
    """A series that produces a typed return result."""

    returns: Sequence[Decimal]

    def normalize(self) -> tuple[Decimal, ...]:
        """Return the normalized series without missing values."""
        return tuple(self.returns)

    @property
    def deduplicated(self) -> list[Decimal]:
        """Return one instance of each distinct observed value."""
        return list(dict.fromkeys(self.normalize()))


@dataclass(frozen=True, slots=True)
class InvalidWindow:
    minimum: int
    maximum: int


@dataclass(frozen=True, slots=True)
class UndefinedCorrelation:
    zero_variance: tuple[ZeroVarianceSide, ...]


type PeriodicReturnResult = Result[tuple[ReturnPoint, ...], InsufficientData]
type VolatilityResult = Result[tuple[Decimal, Decimal], InsufficientData]
type DrawdownResult = Result[
    tuple[tuple[MissingNumeric, ...], Decimal], InsufficientData
]
type MovingAverageResult = Result[tuple[MissingNumeric, ...], InvalidWindow]
type CorrelationResult = Result[
    Decimal, InsufficientData | UndefinedCorrelation
]

_MISSING_REPORT = "__missing__"


def _ordered_points(values: Sequence[SeriesPoint]) -> tuple[SeriesPoint, ...]:
    dates = [point.date for point in values]
    if dates != sorted(dates):
        raise ValueError("series dates must be ordered")
    if len(dates) != len(set(dates)):
        raise ValueError("series dates must be unique")
    return tuple(values)


def returns(values: Sequence[SeriesPoint]) -> PeriodicReturnResult:
    """Return adjacent periodic returns after dropping missing observations."""
    ordered = _ordered_points(values)
    numeric = [point.value for point in ordered if point.value is not None]
    if len(numeric) < _MINIMUM_RETURN_LENGTH:
        return Failure(
            InsufficientData(
                required=_MINIMUM_RETURN_LENGTH, available=len(numeric)
            )
        )
    prior = ordered[0]
    result: list[ReturnPoint] = []
    for point in ordered[1:]:
        if point.value is None:
            continue
        if prior.value is None:
            prior = point
            continue
        result.append(
            ReturnPoint(date=point.date, value=point.value / prior.value - 1)
        )
        prior = point
    return Success(tuple(result))


def volatility(values: Sequence[SeriesPoint]) -> VolatilityResult:
    """Return annualized sample volatility and the annualization factor."""
    ordered = _ordered_points(values)
    numeric = tuple(
        Decimal(point.value) for point in ordered if point.value is not None
    )
    if len(numeric) < _MINIMUM_RETURN_LENGTH:
        return Failure(
            InsufficientData(
                required=_MINIMUM_RETURN_LENGTH, available=len(numeric)
            )
        )
    mean = _mean(numeric)
    variance = Decimal(
        sum((value - mean) ** 2 for value in numeric) / (len(numeric) - 1)
    )
    standard_deviation = variance.sqrt(getcontext())
    return Success(
        (
            standard_deviation * _ANNUALIZATION_FACTOR.sqrt(),
            _ANNUALIZATION_FACTOR,
        )
    )


def drawdown(values: Sequence[SeriesPoint]) -> DrawdownResult:
    """Return aligned drawdowns and maximum drawdown for positive observations."""
    ordered = _ordered_points(values)
    positive = tuple(
        point.value
        for point in ordered
        if point.value is not None and point.value > 0
    )
    if len(positive) < _MINIMUM_DRAWDOWN_LENGTH:
        return Failure(
            InsufficientData(
                required=_MINIMUM_DRAWDOWN_LENGTH, available=len(positive)
            )
        )
    pointwise: list[MissingNumeric] = []
    running_maximum = Decimal(0)
    maximum = Decimal(0)
    saw_positive = False
    for point in ordered:
        value = point.value
        if value is None or value <= 0:
            pointwise.append(None)
            continue
        if not saw_positive:
            saw_positive = True
            running_maximum = value
        else:
            running_maximum = max(running_maximum, value)
        pointwise.append(value / running_maximum - 1)
        maximum = min(maximum, pointwise[-1] or Decimal(0))
    return Success((tuple(pointwise), maximum))


def moving_average(
    values: Sequence[SeriesPoint], window: int
) -> MovingAverageResult:
    """Return aligned moving averages over non-missing observations."""
    if not _MINIMUM_MOVING_AVERAGE_WINDOW <= window <= _MAXIMUM_MOVING_AVERAGE_WINDOW:
        return Failure(
            InvalidWindow(
                minimum=_MINIMUM_MOVING_AVERAGE_WINDOW,
                maximum=_MAXIMUM_MOVING_AVERAGE_WINDOW,
            )
        )
    ordered = _ordered_points(values)
    prior_values: list[Decimal] = []
    result: list[MissingNumeric] = []
    for point in ordered:
        if point.value is None:
            result.append(None)
            continue
        prior_values.append(Decimal(point.value))
        if len(prior_values) >= window:
            result.append(_window_mean(prior_values, window))
        else:
            result.append(None)
    return Success(tuple(result))


def _window_mean(values: Sequence[Decimal], window: int) -> Decimal:
    return sum(values[-window:], Decimal(0)) / window


def correlation(
    left: Sequence[SeriesPoint], right: Sequence[SeriesPoint]
) -> CorrelationResult:
    """Return Pearson correlation over aligned non-missing dates only."""
    ordered_left = _ordered_points(left)
    ordered_right = _ordered_points(right)
    right_by_date = {point.date: point.value for point in ordered_right}
    aligned = tuple(
        (left_point.value, right_by_date[left_point.date])
        for left_point in ordered_left
        if left_point.value is not None
        and right_by_date.get(left_point.date) is not None
    )
    if len(aligned) < _MINIMUM_CORRELATION_LENGTH:
        return Failure(
            InsufficientData(
                required=_MINIMUM_CORRELATION_LENGTH, available=len(aligned)
            )
        )
    left_values: list[Decimal] = [pair[0] for pair in aligned if pair[0] is not None]
    right_values: list[Decimal] = [pair[1] for pair in aligned if pair[1] is not None]
    left_mean = _mean(left_values)
    right_mean = _mean(right_values)
    left_variance = sum(
        ((value - left_mean) ** 2 for value in left_values), Decimal(0)
    )
    right_variance = sum(
        ((value - right_mean) ** 2 for value in right_values), Decimal(0)
    )
    zero_variance: list[ZeroVarianceSide] = []
    if left_variance == 0:
        zero_variance.append("left")
    if right_variance == 0:
        zero_variance.append("right")
    if zero_variance:
        return Failure(
            UndefinedCorrelation(
                zero_variance=tuple(zero_variance)
            )
        )
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left_values, right_values, strict=True)
    )
    denominator = Decimal(left_variance * right_variance)
    return Success(numerator / denominator.sqrt(getcontext()))
