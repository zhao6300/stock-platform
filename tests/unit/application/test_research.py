from __future__ import annotations

from datetime import UTC, datetime

from stock_platform.application.research import ResearchRequest


def test_research_id_is_canonical() -> None:
    value = ResearchRequest("222", "snap-1", datetime(2026, 1, 1, 12, 0, tzinfo=UTC))

    assert value.business_id() == "20260101T12:00:00Z"
