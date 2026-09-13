from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.ingestion import DailyBar
from stock_platform.domain.ingestion import FundNav
from stock_platform.domain.quality import QualityService, QualityStatus, maximum_status


@given(
    security_id=st.text(min_size=1, max_size=20),
    observation_date=st.dates(),
    price=st.decimals(min_value="0.01", max_value="1e12", places=4),
    high=st.decimals(min_value="0.01", max_value="1e12", places=4),
    low=st.decimals(min_value="0.01", max_value="1e12", places=4),
)
def test_daily_bar_quality_issues_record_complete_evidence(
    security_id: str,
    observation_date: date,
    price: Decimal,
    high: Decimal,
    low: Decimal,
) -> None:
    service = QualityService("v1")
    bar = DailyBar(
        observation_date=observation_date,
        open=price,
        high=high,
        low=low,
        close=price,
        volume=Decimal("-1"),
        turnover=Decimal("-1"),
        currency="USD",
    )

    for issue, expected_status in service.daily_bar_status(bar, security_id):
        assert issue.security_id == security_id
        assert issue.observation_date == observation_date
        assert issue.rule.version_id == "v1"
        assert issue.rule.rule_id
        assert issue.affected_field
        assert issue.observed_value is not None
        assert issue.rule.status == expected_status


@given(
    observation_date=st.dates(),
    quantity=st.integers(min_value=0, max_value=3),
)
def test_fund_nav_quality_evidence_includes_each_field(  # noqa: PLR0913
    observation_date: date,
    quantity: int,
) -> None:
    service = QualityService("v1")
    cumulative_nav = None if quantity == 0 else Decimal(quantity)
    fund = FundNav(
        observation_date=observation_date,
        cumulative_nav=cumulative_nav,
        unit_nav=Decimal(1),
        currency="USD",
    )
    for issue, expected_status in service.fund_nav_status(
        fund,
        "SEC-1",
        expected_on_calendar=True,
    ):
        assert issue.security_id == "SEC-1"
        assert issue.observation_date == observation_date
        assert issue.rule.version_id == "v1"
        assert issue.rule.rule_id
        assert issue.affected_field in {"unit_nav", "cumulative_nav"}
        assert issue.rule.status == expected_status
