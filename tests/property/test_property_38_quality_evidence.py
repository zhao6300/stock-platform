from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.ingestion import DailyBar
from stock_platform.domain.quality import QualityService


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

    for issue in service.daily_bar_issues(bar, security_id):
        assert issue.security_id == security_id
        assert issue.observation_date == observation_date
        assert issue.rule.version_id == "v1"
        assert issue.rule.rule_id
        assert issue.affected_field
        assert issue.observed_value
