from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

from stock_platform.domain.adjustments import (
    AdjustmentFactorPoint,
    AdjustmentFactorSeries,
    AdjustmentFactorSource,
    AdjustmentMode,
    AdjustmentService,
    PricePoint,
    fund_nav_fallback,
)
from stock_platform.domain.common import Failure, Success
from stock_platform.domain.ingestion import FundNav


def _factors() -> AdjustmentFactorSeries:
    return AdjustmentFactorSeries(
        version_id="factors-v1",
        source_type=AdjustmentFactorSource.CORPORATE_ACTION,
        source_id="corporate-action-1",
        retrieved_at=datetime(2025, 12, 31, tzinfo=UTC),
        points=(
            AdjustmentFactorPoint(date(2025, 1, 1), Decimal("3")),
            AdjustmentFactorPoint(date(2025, 1, 2), Decimal("2")),
            AdjustmentFactorPoint(date(2025, 1, 3), Decimal("1")),
        ),
    )


def _raw_series(dates: tuple[date, ...]) -> tuple[PricePoint, ...]:
    prices = {date(2025, 1, 1): Decimal("10"), date(2025, 1, 2): Decimal("20"), date(2025, 1, 3): Decimal("30")}
    return tuple(PricePoint(observation_date=value, raw_price=prices[value]) for value in dates)


def test_adjusted_series_discloses_mode_factor_source_and_version() -> None:
    result = AdjustmentService().apply(
        mode=AdjustmentMode.FORWARD_ADJUSTED,
        modes=(),
        raw_series=_raw_series((date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3))),
        factors=_factors(),
    )

    assert isinstance(result, Success)
    assert result.value.mode is AdjustmentMode.FORWARD_ADJUSTED
    assert result.value.factor_source is AdjustmentFactorSource.CORPORATE_ACTION
    assert result.value.factor_source_id == "corporate-action-1"
    assert result.value.factor_version_id == "factors-v1"
    assert [point.raw_price for point in result.value.values] == [Decimal("30"), Decimal("40"), Decimal("30")]


def test_adjusted_subrange_matches_full_series_slice() -> None:
    service = AdjustmentService()
    factors = _factors()
    full = service.apply(
        mode=AdjustmentMode.BACKWARD_ADJUSTED,
        modes=(),
        raw_series=_raw_series((date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3))),
        factors=factors,
    )
    subrange = service.apply(
        mode=AdjustmentMode.BACKWARD_ADJUSTED,
        modes=(),
        raw_series=_raw_series((date(2025, 1, 2), date(2025, 1, 3))),
        factors=factors,
    )

    assert isinstance(full, Success)
    assert isinstance(subrange, Success)
    assert subrange.value.values == full.value.values[-2:]


def test_rejected_factor_returns_no_values_and_names_bad_dates() -> None:
    factors = _factors()
    factors = replace(
        factors,
        points=(
            factors.points[0],
            replace(factors.points[1], factor=Decimal("0")),
            factors.points[2],
        ),
    )

    result = AdjustmentService().apply(
        mode=AdjustmentMode.FORWARD_ADJUSTED,
        modes=(),
        raw_series=_raw_series((date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3))),
        factors=factors,
    )

    assert isinstance(result, Failure)
    assert result.error.invalid_dates == (date(2025, 1, 2),)
    assert result.error.missing_dates == ()


def test_provider_cumulative_nav_absence_has_explicit_fallback() -> None:
    absent = fund_nav_fallback(
        FundNav(
            observation_date=date(2025, 1, 1),
            unit_nav=Decimal("10"),
            cumulative_nav=None,
            currency="CNY",
        )
    )
    present = fund_nav_fallback(
        FundNav(
            observation_date=date(2025, 1, 1),
            unit_nav=Decimal("10"),
            cumulative_nav=Decimal("12"),
            currency="CNY",
        )
    )

    assert isinstance(absent, Success)
    assert absent.value.cumulative_nav is None
    assert absent.value.cumulative_nav_available is False
    assert absent.value.cumulative_nav_status == "UNAVAILABLE"
    assert isinstance(present, Success)
    assert present.value.cumulative_nav == Decimal("12")
    assert present.value.cumulative_nav_available is True
    assert present.value.cumulative_nav_status == "AVAILABLE"
