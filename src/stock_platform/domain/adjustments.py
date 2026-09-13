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
from stock_platform.domain.ingestion import FundNav
from stock_platform.domain.quality import QualityStatus


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
        if not isinstance(self.source_type, AdjustmentFactorSource):
            raise ValueError("adjustment factor source type is missing")
        if not self.version_id or not self.source_id:
            raise ValueError("adjustment factors must have a source and version")

    def validate_source(self) -> bool:
        """Return whether the factor carries exactly one complete provenance."""
        return self.source_type in AdjustmentFactorSource and self.source_id != ""


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
    missing_dates: tuple[date, ...] = ()
    invalid_dates: tuple[date, ...] = ()
    quality_status: QualityStatus = QualityStatus.REJECTED


@dataclass(frozen=True, slots=True)
class AdjustedSeries:
    """A derived series with the one factor version that produced it."""

    mode: AdjustmentMode
    factor_source: AdjustmentFactorSource
    factor_source_id: str
    factor_version_id: str
    values: tuple[PricePoint, ...]


@dataclass(frozen=True, slots=True)
class FundNavPresentation:
    """A provider-owned NAV row with an explicit cumulative NAV state."""

    observation_date: date
    unit_nav: Decimal
    cumulative_nav: Decimal | None
    cumulative_nav_available: bool
    cumulative_nav_status: str


type AdjustmentResult = Result[AdjustedSeries, InvalidMode | InvalidFactor]
type FundNavPresentationResult = Result[FundNavPresentation, str]


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


def _price_points(
    series: Sequence[PricePoint],
) -> tuple[PricePoint, ...]:
    dates = [point.observation_date for point in series]
    if dates != sorted(dates):
        raise AdjustmentValidationError("prices must be ordered")
    if len(dates) != len(set(dates)):
        raise AdjustmentValidationError("prices must be unique")
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
        if len(selected_modes) != 1:
            return Failure(InvalidMode(self.permitted_modes))
        selected = selected_modes[0]
        if selected not in self.permitted_modes:
            return Failure(InvalidMode(self.permitted_modes))
        mode = selected

        if mode is AdjustmentMode.UNADJUSTED:
            return Success(
                AdjustedSeries(
                    mode=mode,
                    factor_source=factors.source_type,
                    factor_source_id=factors.source_id,
                    factor_version_id=factors.version_id,
                    values=tuple(raw_series),
                )
            )

        try:
            sorted_factors = _factor_points(factors.points)
        except AdjustmentValidationError:
            return Failure(InvalidFactor(factors.version_id))
        if not sorted_factors:
            return Failure(InvalidFactor(factors.version_id))
        factor_by_date = {point.effective_date: point.factor for point in sorted_factors}
        invalid_dates = tuple(
            factor.effective_date
            for factor in sorted_factors
            if not factor.factor.is_finite() or factor.factor <= 0
        )
        price_points = _price_points(raw_series)
        missing_dates = tuple(
            point.observation_date
            for point in price_points
            if point.observation_date not in factor_by_date
        )
        if invalid_dates or missing_dates:
            return Failure(InvalidFactor(factors.version_id, missing_dates, invalid_dates))
        adjusted = self._apply_factors(_price_points(raw_series), sorted_factors, mode)
        return Success(
            AdjustedSeries(
                mode=mode,
                factor_source=factors.source_type,
                factor_source_id=factors.source_id,
                factor_version_id=factors.version_id,
                values=adjusted,
            )
        )

    def _apply_factors(
        self,
        raw_series: Sequence[PricePoint],
        factors: tuple[AdjustmentFactorPoint, ...],
        mode: AdjustmentMode,
    ) -> tuple[PricePoint, ...]:
        """Apply the selected complete factor series without a partial result."""
        factor_by_date = {factor.effective_date: factor.factor for factor in factors}
        if any(not factor.factor.is_finite() or factor.factor <= 0 for factor in factors):
            raise AdjustmentValidationError("adjustment factors must be positive")
        missing = [
            point.observation_date
            for point in raw_series
            if point.observation_date not in factor_by_date
        ]
        if missing:
            raise AdjustmentValidationError(
                f"missing adjustment dates: {', '.join(date.isoformat() for date in missing)}"
            )
        if not factors:
            raise AdjustmentValidationError("adjustment factors must not be empty")
        if mode is AdjustmentMode.FORWARD_ADJUSTED:
            anchor = factors[-1].factor
        else:
            anchor = factors[0].factor
        return tuple(
            PricePoint(
                observation_date=price_point.observation_date,
                raw_price=price_point.raw_price
                * factor_by_date[price_point.observation_date]
                / anchor,
            )
            for price_point in raw_series
        )


def fund_nav_fallback(observation: FundNav) -> FundNavPresentationResult:
    """Return provider values and leave cumulative NAV unavailable when absent."""
    if observation.cumulative_nav is None:
        return Success(
            FundNavPresentation(
                observation_date=observation.observation_date,
                unit_nav=observation.unit_nav,
                cumulative_nav=None,
                cumulative_nav_available=False,
                cumulative_nav_status="UNAVAILABLE",
            )
        )
    return Success(
        FundNavPresentation(
            observation_date=observation.observation_date,
            unit_nav=observation.unit_nav,
            cumulative_nav=observation.cumulative_nav,
            cumulative_nav_available=True,
            cumulative_nav_status="AVAILABLE",
        )
    )
