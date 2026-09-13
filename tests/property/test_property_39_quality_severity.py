from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.ingestion import DailyBar
from stock_platform.domain.quality import QualityService, QualityStatus, maximum_status


@given(
    observation_date=st.dates(),
    price=st.decimals(min_value="0.01", max_value="1e12", places=4),
    open_on_calendar=st.none() | st.booleans(),
    rule_inputs=st.fixed_dictionaries(
        {
            "invalid_price": st.booleans(),
            "invalid_total": st.booleans(),
            "inverted_ohlc": st.booleans(),
        }
    ),
)
def test_quality_status_is_the_maximum_applicable_severity(
    observation_date: date,
    price: Decimal,
    open_on_calendar: bool | None,
    rule_inputs: dict[str, bool],
) -> None:
    invalid_price = rule_inputs["invalid_price"]
    invalid_total = rule_inputs["invalid_total"]
    inverted_ohlc = rule_inputs["inverted_ohlc"]
    service = QualityService("v1")
    high = price
    low = price
    bar = DailyBar(
        observation_date=observation_date,
        open=-price if invalid_price else price,
        high=price * 2 if inverted_ohlc else high,
        low=price * 3 if inverted_ohlc else low,
        close=price,
        volume=-price if invalid_total else price,
        turnover=-price if invalid_total else price,
        currency="USD",
    )

    issues = service.daily_bar_issues(bar, "SEC-1", open_on_calendar=open_on_calendar)
    status = maximum_status(*(issue.rule.status for issue in issues), QualityStatus.VALID)
    if issues:
        assert status == max(
            (issue.rule.status for issue in issues),
            key=lambda value: {"VALID": 0, "WARNING": 1, "REJECTED": 2}[value],
        )
    if open_on_calendar is None and not (invalid_price or invalid_total or inverted_ohlc):
        assert status == QualityStatus.WARNING
        assert all(
            issue.missing_input == "CALENDAR"
            for issue in issues
        )
    elif invalid_price or invalid_total or inverted_ohlc or open_on_calendar is False:
        assert status == QualityStatus.REJECTED
    else:
        assert status == QualityStatus.VALID
