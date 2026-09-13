from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis.strategies import integers

from stock_platform.domain.backtesting import (
    BacktestEngine,
    CostModel,
    DailyBar,
    TradingCalendarVersion,
)


class PassiveStrategy:
    api_version = "daily.v1"
    required_capabilities = frozenset()

    def on_day_close(self, context):
        return []


@given(
    universe_size=integers(min_value=2, max_value=4),
    benchmark_size=integers(min_value=2, max_value=4),
)
def test_coverage_from_backtest_disclosure(
    universe_size: int,
    benchmark_size: int,
) -> None:
    calendar_dates = sorted({date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6)})[:universe_size]
    calendar = TradingCalendarVersion("calendar-v1", "XSHG", frozenset(calendar_dates))
    bars = [
        DailyBar("0", date(2026, 1, 2), Decimal("25")),
        DailyBar("1", date(2026, 1, 5), Decimal("50")),
    ]
    engine = BacktestEngine(
        strategy=PassiveStrategy(),
        calendar=calendar,
        bars=bars,
        tradability=[],
        cost_model=CostModel(
            Decimal("0.01"),
            Decimal("0.02"),
            Decimal("0.0001"),
            Decimal("0.01"),
            "CNY",
        ),
        missing_price_policy="FIVE_SESSION_FALLBACK",
        initial_cash=Decimal("1000"),
        initial_positions={},
        point_in_time_membership=None,
        adjustment_mode="UNADJUSTED",
        benchmark="NONE",
    )
    result = engine.run().value
    assert result.disclosure.data_start == date(2026, 1, 2)
    assert result.disclosure.data_end >= date(2026, 1, 5)
    assert result.disclosure.universe == {"0", "1"}
    assert result.disclosure.benchmark == "NONE"
    assert result.disclosure.calendar_version == calendar.version_id
    assert result.disclosure.adjustment_mode == "UNADJUSTED"
    assert result.disclosure.cost_model.currency == "CNY"
    assert result.disclosure.missing_price_policy == "FIVE_SESSION_FALLBACK"
    assert result.survivorship_warning is True
