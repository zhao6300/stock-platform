from __future__ import annotations

from datetime import date
from decimal import Decimal

from stock_platform.domain.backtesting import (
    BacktestEngine,
    CostModel,
    DailyBar,
    TradingCalendarVersion,
)


class Unsupported:
    api_version = "daily.v1"
    required_capabilities = frozenset({"short_selling"})
    def on_day_close(self, context) -> None:
        raise AssertionError("strategy must not be called")

def test_unsupported_capabilities_preserve_initial_state() -> None:
    dates = (date(2026, 1, 2), date(2026, 1, 5))
    calendar = TradingCalendarVersion("calendar-v1", "XSHG", frozenset(dates))
    bars = [DailyBar("A", date(2026, 1, 2), Decimal(100))]
    engine = BacktestEngine(
        strategy=Unsupported(),
        calendar=calendar,
        bars=bars,
        tradability=[],
        cost_model=CostModel(Decimal(0), Decimal(0), Decimal(0), Decimal(0), "CNY"),
        missing_price_policy="UNAVAILABLE",
        initial_cash=Decimal(100),
        initial_positions={"A": Decimal(1)},
    )
    report = engine.run().value
    assert report.simulated_execution == ()
    assert report.disclosure.data_end == dates[-1]
    assert engine.initial_cash == Decimal(100)
    assert engine.initial_positions == {"A": Decimal(1)}
