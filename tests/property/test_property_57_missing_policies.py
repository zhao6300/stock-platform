from __future__ import annotations

from datetime import date
from decimal import Decimal

from stock_platform.domain.backtesting import (
    BacktestEngine,
    CostModel,
    DailyBar,
    DayContext,
    TradingCalendarVersion,
)


class Passive:
    api_version = "daily.v1"
    required_capabilities = frozenset()
    def on_day_close(self, context: DayContext) -> None:
        return ()

def missing_report(policy: str) -> tuple:
    dates = (date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 12))
    calendar = TradingCalendarVersion("calendar-v1", "XSHG", frozenset(dates))
    bars = [DailyBar("A", dates[0], Decimal(100))]
    engine = BacktestEngine(
        strategy=Passive(),
        calendar=calendar,
        bars=bars,
        tradability=[],
        cost_model=CostModel(Decimal(0), Decimal(0), Decimal(0), Decimal(0), "CNY"),
        missing_price_policy=policy,
        initial_cash=Decimal(100),
        initial_positions={"A": Decimal(1)},
    )
    report = engine.run().value
    return report.portfolio_valuation[-1], report.performance_calculation[-1]

def test_unavailable_and_five_session_policies_are_exhaustive() -> None:
    unavailable, unavailable_performance = missing_report("UNAVAILABLE")
    fallback, fallback_performance = missing_report("FIVE_SESSION_FALLBACK")
    assert unavailable.close is None and unavailable.valuation_available is False
    assert unavailable_performance.available is False
    assert fallback.close == Decimal(100)
    assert fallback.source_date == date(2026, 1, 2)
    assert fallback_performance.portfolio_value == Decimal(200)
