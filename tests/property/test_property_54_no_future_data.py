from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import ClassVar

from stock_platform.domain.backtesting import (
    BacktestEngine,
    CostModel,
    DailyBar,
    DayContext,
    TradingCalendarVersion,
)


class ProbeStrategy:
    api_version = "daily.v1"
    required_capabilities = frozenset()
    seen_dates: ClassVar[list[date]] = []

    def on_day_close(self, context: DayContext) -> None:
        self.seen_dates.append(context.trading_date)
        return ()

def test_market_view_and_strategy_context_are_no_future() -> None:
    dates = (date(2026, 1, 2), date(2026, 1, 5))
    calendar = TradingCalendarVersion("calendar-v1", "XSHG", frozenset(dates))
    bars = [DailyBar("A", dates[-1], Decimal(100))]
    strategy = ProbeStrategy()
    engine = BacktestEngine(
        strategy=strategy,
        calendar=calendar,
        bars=bars,
        tradability=[],
        cost_model=CostModel(Decimal(0), Decimal(0), Decimal(0), Decimal(0), "CNY"),
        missing_price_policy="UNAVAILABLE",
        initial_cash=Decimal(100),
        initial_positions={},
    )
    report = engine.run().value
    assert strategy.seen_dates == list(dates)
    assert report.disclosure.data_start == dates[0]
    assert report.disclosure.calendar_version == calendar.version_id
