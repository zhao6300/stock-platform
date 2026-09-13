from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from stock_platform.domain.common import (
    Failure,
    Result,
    Success,
    ensure_timezone_aware,
)


class AdjustmentMode(StrEnum):
    """A documented price-basis selection."""

    UNADJUSTED = "UNADJUSTED"
    FORWARD_ADJUSTED = "FORWARD_ADJUSTED"
    BACKWARD_ADJUSTED = "BACKWARD_ADJUSTED"


class AdjustmentFactorSource(StrEnum):
    """The single kind of provenance that created a factor series."""

    PROVIDER = "PROVIDER"
    CORPORATE_ACTION = "CORPORATE_ACTION"


PERMITTED_MODES = tuple(AdjustmentMode)


@dataclass(frozen=True, slots=True)
class PricePoint:
    """An immutable provider-supplied price at one business date."""

    observation_date: date
    raw_price: Decimal

    @property
    def raw_value(self) -> PricePoint:
        return self

    @property
    def raw_values(self) -> tuple[PricePoint, ...]:
        return (self,)


@dataclass(frozen=True, slots=True)
class RawPriceSeries:
    """A provider-owned price series preserved by every adjustment call."""

    values: tuple[PricePoint, ...]

    @property
    def raw_values(self) -> tuple[PricePoint, ...]:
        return self.values


@dataclass(frozen=True, slots=True)
class AdjustmentFactorPoint:
    """One positive factor for exactly one effective date."""

    effective_date: date
    factor: Decimal


@dataclass(frozen=True, slots=True)
class AdjustmentFactorSeries:
    """A complete, positive, versioned factor series."""

    version_id: str
    source_type: AdjustmentFactorSource
    source_id: str
    retrieved_at: datetime
    points: tuple[AdjustmentFactorPoint, ...]

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.retrieved_at)
        if not self.version_id or not self.source_id:
            raise ValueError("adjustment factors must have a source and version")
        if any(point.factor <= 0 for point in self.points):
            raise ValueError("adjustment factors must be positive")


class AdjustmentValidationError(ValueError):
    """Any adjustment request that can safely publish no derived prices."""


@dataclass(frozen=True, slots=True)
class InvalidMode:
    """A safe mode rejection that names every permitted mode."""

    permitted_modes: tuple[AdjustmentMode, ...]


@dataclass(frozen=True, slots=True)
class InvalidFactor:
    """The selected factor version failed all-or-nothing validation."""

    version_id: str


@dataclass(frozen=True, slots=True)
class AdjustedSeries:
    """A derived series with the one factor version that produced it."""

    mode: AdjustmentMode
    factor_version_id: str
    values: tuple[PricePoint, ...]


type AdjustmentResult = Result[AdjustedSeries, InvalidMode | InvalidFactor]


def _sorted_unique(
    series: Sequence[PricePoint] | Sequence[AdjustmentFactorPoint],
) -> tuple[PricePoint, ...] | tuple[AdjustmentFactorPoint, ...]:
    dates = [
        point.observation_date if isinstance(point, PricePoint) else point.effective_date
        for point in series
    ]
    if dates != sorted(dates):
        raise AdjustmentValidationError("dates must be ordered")
    if len(dates) != len(set(dates)):
        raise AdjustmentValidationError("dates must be unique")
    return tuple(series)  # type: ignore[return-value]


def _factor_points(
    series: Sequence[AdjustmentFactorPoint],
) -> tuple[AdjustmentFactorPoint, ...]:
    dates = [point.effective_date for point in series]
    if dates != sorted(dates):
        raise AdjustmentValidationError("dates must be ordered")
    if len(dates) != len(set(dates)):
        raise AdjustmentValidationError("dates must be unique")
    return tuple(series)


class AdjustmentService:
    """Transform owned raw prices without ever changing their source series."""

    def __init__(self, permitted_modes: tuple[AdjustmentMode, ...] = PERMITTED_MODES) -> None:
        self.permitted_modes = permitted_modes

    def apply(
        self,
        *,
        mode: AdjustmentMode | None,
        modes: Sequence[AdjustmentMode],
        raw_series: Sequence[PricePoint],
        factors: AdjustmentFactorSeries,
    ) -> AdjustmentResult:
        selected_modes = modes if mode is None else (mode, *modes)
        mode = selected_modes[0] if selected_modes and len(selected_modes) == 1 else None
        if selected_modes.count(AdjustmentMode.UNADJUSTED) > 1:
            return Failure(InvalidMode(self.permitted_modes))
        if mode is None or mode not in self.permitted_modes:
            return Failure(InvalidMode(self.permitted_modes))

        if mode is AdjustmentMode.UNADJUSTED:
            return Success(AdjustedSeries(mode, factors.version_id, tuple(raw_series)))

        if not factors.points:
            return Failure(InvalidFactor(factors.version_id))
        sorted_factors = _factor_points(factors.points)
        adjusted = self._apply_factors(raw_series, sorted_factors, mode)
        return Success(
            AdjustedSeries(mode=mode, factor_version_id=factors.version_id, values=adjusted)
        )

    def _apply_factors(
        self,
        raw_series: Sequence[PricePoint],
        factors: tuple[AdjustmentFactorPoint, ...],
        mode: AdjustmentMode,
    ) -> tuple[PricePoint, ...]:
        """Apply the required complete factor series to unmodified raw prices."""
        if any(price_point.raw_price <= 0 for price_point in raw_series):
            raise AdjustmentValidationError("raw prices must be positive")
        factor_by_date = {factor.effective_date: factor.factor for factor in factors}
        consumers: dict[date, PricePoint] = {}
        for price_point in raw_series:
            price_dates = price_point.raw_price
            if not isinstance(price_dates, Decimal):
                raise AdjustmentValidationError("raw prices must be Decimal values")
        if all(point.observation_date not in factor_by_date for point in raw_series):
            raise AdjustmentValidationError("factors are incomplete")
        if mode is AdjustmentMode.FORWARD_ADJUSTED:
            anchor = factor_by_date[factors[-1].effective_date]
        else:
            anchor = factors[-1].factor
        return tuple(
            PricePoint(
                observation_date=observation_date,
                raw_price=price_point.raw_price * factor_by_date[observation_date] / anchor,
            )
            for observation_date in consumers
        )
