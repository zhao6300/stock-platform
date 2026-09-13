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
    TradingCalendarVersion,
)


class Buy:
    api_version = "daily.v1"
    required_capabilities = frozenset()

    def on_day_close(self, context: DayContext) -> tuple[Signal, ...]:
        return (Signal("A", "BUY", Decimal(1)),)


def test_fills_reconcile_to_cost_data() -> None:
    trading_date = date(2026, 1, 2)
    calendar = TradingCalendarVersion("calendar-v1", "XSHG", frozenset([trading_date, date(2026, 1, 5)]))
    cost_model = CostModel(
        commission_rate=Decimal("0.01"),
        tax_rate=Decimal("0.02"),
        slippage_bps=Decimal(10),
        minimum_fee=Decimal(1),
        currency="CNY",
    )
    engine = BacktestEngine(
        strategy=Buy(),
        calendar=calendar,
        bars=[DailyBar("A", trading_date, Decimal(100)), DailyBar("A", date(2026, 1, 5), Decimal(100))],
        tradability=[Tradability("A", trading_date, "OPEN"), Tradability("A", date(2026, 1, 5), "OPEN")],
        cost_model=cost_model,
        missing_price_policy="FIVE_SESSION_FALLBACK",
        initial_cash=Decimal(1000),
        initial_positions={},
    )
    report = engine.run().value
    trade = report.simulated_execution[0]
    assert trade.filled_quantity == Decimal(1)
    assert trade.execution_price == Decimal("100.1000")
    assert trade.gross_value == Decimal("100.10")
    assert trade.cost_components["commission"] == Decimal(1)
    assert trade.cost_components["tax"] == Decimal("2.00")
    assert trade.total_cost == Decimal("3.00")
    assert trade.net_cash_change == Decimal("103.10")
    assert engine.entries[-1].cash_delta == Decimal("-103.10")
    assert engine.entries[-1].position_delta == Decimal(1)
