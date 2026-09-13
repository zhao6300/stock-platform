from __future__ import annotations

from datetime import date
from decimal import Decimal

from stock_platform.domain.backtesting import (
    BacktestEngine,
    CostModel,
    DailyBar,
    DayContext,
    Signal,
    Tradability,
    TradeRecord,
    TradingCalendarVersion,
)


class Sell:
    api_version = "daily.v1"
    required_capabilities = frozenset()

    def on_day_close(self, context: DayContext) -> tuple[Signal, ...]:
        return (Signal("A", "SELL", Decimal(1)),)


def blocked_case(status: str) -> TradeRecord:
    trading_date = date(2026, 1, 2)
    execution_date = date(2026, 1, 5)
    calendar = TradingCalendarVersion(
        "calendar-v1", "XSHG", frozenset([trading_date, execution_date])
    )
    engine = BacktestEngine(
        strategy=Sell(),
        calendar=calendar,
        bars=[
            DailyBar("A", trading_date, Decimal(100)),
            DailyBar("A", date(2026, 1, 5), Decimal(100)),
        ],
        tradability=[Tradability("A", date(2026, 1, 5), status)],
        cost_model=CostModel(Decimal(0), Decimal(0), Decimal(0), Decimal(0), "CNY"),
        missing_price_policy="FIVE_SESSION_FALLBACK",
        initial_cash=Decimal(100),
        initial_positions={"A": Decimal(1)},
    )
    report = engine.run().value
    return report.simulated_execution[0]


def test_blocked_and_no_fill_are_atomic() -> None:
    for status in ("SUSPENDED", "PRICE_LIMITED", "TERMINATED", "UNKNOWN"):
        trade = blocked_case(status)
        assert trade.filled_quantity == Decimal(0)
        assert trade.reason == status
        assert trade.net_cash_change == Decimal(0)
