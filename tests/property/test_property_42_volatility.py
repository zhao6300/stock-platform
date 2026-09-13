from __future__ import annotations

from datetime import date
from decimal import Decimal

from stock_platform.domain.analytics import volatility
from stock_platform.domain.fundamentals import SeriesPoint


def test_only_will_factor_in_calculated_values() -> None:
    result = volatility(
        [
            SeriesPoint(date(2025, 1, 1), value=Decimal("1")),
            SeriesPoint(date(2025, 1, 2), value=Decimal("2")),
        ],
    )

    assert result.value[1] == Decimal("252")
