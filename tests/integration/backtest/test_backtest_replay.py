from __future__ import annotations

from datetime import date
from decimal import Decimal

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


def test_backtest_report_sections_are_pinned() -> None:
    calendar = TradingCalendarVersion(
        version_id="calendar-v1",
        market="XSHG",
        open_dates=frozenset([date(2026, 1, 2)]),
    )
    engine = BacktestEngine(
        strategy=PassiveStrategy(),
        calendar=calendar,
        bars=[DailyBar("A", date(2026, 1, 2), Decimal(100))],
        tradability=[],
        cost_model=CostModel(
            Decimal("0.01"),
            Decimal("0.02"),
            Decimal("0.0001"),
            Decimal("0"),
            "CNY",
        ),
        missing_price_policy="UNAVAILABLE",
        initial_cash=Decimal(1000),
        initial_positions={},
    )

    report = engine.run().value

    assert report.disclosure.data_start == date(2026, 1, 2)
    assert report.disclosure.data_end == date(2026, 1, 2)
    assert report.survivorship_warning is True
    assert report.affected_quality == ()
