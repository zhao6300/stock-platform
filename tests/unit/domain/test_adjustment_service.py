from __future__ import annotations

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


def _factor_series(
    *,
    points: tuple[AdjustmentFactorPoint, ...],
    source_type: int,
    source_id: str = "provider-1",
) -> AdjustmentFactorSeries:
    return AdjustmentFactorSeries(
        version_id="factors-v1",
        source_type=source_type,
        source_id=source_id,
        retrieved_at=datetime(2025, 12, 1, tzinfo=UTC),
        points=points,
)


def test_adjustment_factor_preserves_raw_value() -> None:
    raw = (PricePoint(date(2025, 1, 1), Decimal("10")),)
    factors = _factor_series(
        points=(AdjustmentFactorPoint(date(2025, 1, 1), Decimal(2)),),
        source_type=AdjustmentFactorSource.PROVIDER,
    )

    adjusted = AdjustmentService().apply(
        mode=AdjustmentMode.FORWARD_ADJUSTED,
        modes=(),
        raw_series=raw,
        factors=factors,
    )

    assert isinstance(adjusted, Success)


def test_adjustment_factor_incomplete_series_rejects() -> None:
    raw = (
        PricePoint(date(2025, 1, 1), Decimal("10")),
        PricePoint(date(2025, 1, 2), Decimal("12")),
    )
    factors = _factor_series(
        points=(AdjustmentFactorPoint(date(2025, 1, 1), Decimal(1)),),
        source_type=AdjustmentFactorSource.PROVIDER,
        source_id="source-1",
    )

    adjusted = AdjustmentService().apply(
        mode=AdjustmentMode.FORWARD_ADJUSTED,
        modes=(),
        raw_series=raw,
        factors=factors,
    )

    assert isinstance(adjusted, Failure)


def test_fund_nav_fallback_preserves_provider_values() -> None:
    unit_nav = Decimal("10")
    cumulative_nav = Decimal("12")
    observation = FundNav(
        observation_date=date(2025, 1, 1),
        unit_nav=unit_nav,
        cumulative_nav=cumulative_nav,
        currency="CNY",
    )

    result = fund_nav_fallback(observation)

    assert isinstance(result, Success)
    assert result.value.unit_nav == unit_nav
    assert result.value.cumulative_nav == cumulative_nav
    assert result.value.cumulative_nav_available is True
    assert result.value.cumulative_nav_status == "AVAILABLE"


def test_fund_nav_fallback_marks_confirmation_absent() -> None:
    unit_nav = Decimal("10")
    observation = FundNav(
        observation_date=date(2025, 1, 1),
        unit_nav=unit_nav,
        cumulative_nav=None,
        currency="CNY",
    )

    result = fund_nav_fallback(observation)

    assert isinstance(result, Success)
    assert result.value.unit_nav == unit_nav
    assert result.value.cumulative_nav is None
    assert result.value.cumulative_nav_available is False
    assert result.value.cumulative_nav_status == "UNAVAILABLE"
