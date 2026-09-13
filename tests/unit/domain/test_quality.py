from __future__ import annotations

from datetime import date

from stock_platform.domain.quality import QualityIssue, QualityRule, QualityStatus


def test_quality_report_uses_check_scope_and_rule_version() -> None:
    issue = QualityIssue(
        security_id="SEC-1",
        observation_date=date(2026, 1, 2),
        rule=QualityRule(
            rule_id="DAILY_BAR_POSITIVE_PRICE",
            version_id="v1",
            status=QualityStatus.REJECTED,
        ),
        affected_field="open",
        observed_value="0",
        missing_input=None,
    )

    assert issue.security_id == "SEC-1"
    assert issue.observation_date == date(2026, 1, 2)
    assert issue.rule.rule_id == "DAILY_BAR_POSITIVE_PRICE"
    assert issue.rule.version_id == "v1"
    assert issue.rule.status == QualityStatus.REJECTED
    assert issue.affected_field == "open"
    assert issue.observed_value == "0"
    assert issue.missing_input is None
