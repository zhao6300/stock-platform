from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.ingestion import DailyBar
from stock_platform.domain.quality import QualityService


@given(
    scope=st.text(min_size=1, max_size=30),
    observation_date=st.dates(),
)
def test_quality_reports_are_complete_aggregations(
    scope: str,
    observation_date: date,
) -> None:
    service = QualityService("v1")
    bar = DailyBar(
        observation_date=observation_date,
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=Decimal("1"),
        turnover=Decimal("1"),
        currency="USD",
    )
    issues = service.daily_bar_issues(bar, "SEC-1")
    generated_at = datetime.now(tz=UTC)
    report = service.report(scope, issues, generated_at=generated_at)

    assert report.scope == scope
    assert report.rule_version_id == service.rule_version_id
    assert report.issues == issues
    assert report.generated_at == generated_at
