from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis.strategies import decimals

from stock_platform.domain.backtesting import (
    BacktestEngine,
    CostModel,
    DailyBar,
    Signal,
    TradingCalendarVersion,
)


class FixedStrategy:
    api_version = "daily.v1"
    required_capabilities = frozenset()

    def on_day_close(self, context):
        return (
            Signal("A", "SELL" if context.positions.get("A") else "BUY", Decimal(1)),
        )


@given(
    quantity=decimals(min_value=Decimal("0.01"), max_value=Decimal("1_000.00")),
    price=decimals(min_value=Decimal("0.01"), max_value=Decimal("1_000.00")),
)
def test_lighter_events_stay_solvent_and_long_only(
    quantity: Decimal,
    price: Decimal,
) -> None:
    calendar = TradingCalendarVersion("calendar-v1", "XSHG", frozenset({date(2026, 1, 2)}))
    engine = BacktestEngine(
        strategy=FixedStrategy(),
        calendar=calendar,
        bars=[DailyBar("A", date(2026, 1, 2), price)],
        tradability=[],
        cost_model=CostModel(Decimal(0), Decimal(0), Decimal(0), Decimal(0), "CNY"),
        missing_price_policy="UNAVAILABLE",
        initial_cash=Decimal(1000),
        initial_positions={},
    )
    result = engine.run().value
    cash = Decimal(1000)
    positions = {}
    for trade in result.simulated_execution:
        cash += trade.net_cash_change
        positions[trade.instrument] = positions.get(trade.instrument, Decimal(0)) + trade.position_delta
        assert cash >= 0
        assert positions[trade.instrument] >= 0
