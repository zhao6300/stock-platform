from __future__ import annotations

from datetime import UTC, datetime

import pytest

from stock_platform.domain.quality import QualityReport


def test_quality_report_rejects_invalid_scope_or_rule_version() -> None:
    now = datetime.now(tz=UTC)
    for scope in ("", None):
        for rule_version_id in ("", None):
            with pytest.raises(ValueError):
                QualityReport(scope, rule_version_id, (), now)


def test_quality_report_uses_check_scope_and_rule_version() -> None:
    report = QualityReport.from_scope(
        scope="SEC-1/FUND_NAV/2026-01-02",
        rule_version_id="v1",
        issues=(),
        generated_at=datetime.now(tz=UTC),
    )

    assert report.scope == "SEC-1/FUND_NAV/2026-01-02"
    assert report.rule_version_id == "v1"
    assert report.issues == ()
