from __future__ import annotations

from datetime import UTC, datetime

from stock_platform.domain.research import canonical_business_id


def test_canonical_business_id_uses_utc() -> None:
    value = canonical_business_id(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))

    assert value == "20260101T12:00:00Z"
