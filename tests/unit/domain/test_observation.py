from __future__ import annotations

from datetime import UTC, date, datetime

from stock_platform.domain.observation import Observation, ObservationCode


def test_observation_accepts_unique_ordered_dates() -> None:
    observation = Observation(
        code=ObservationCode(code="test", kind="DAILY_BAR"),
        provider="fake",
        retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
        dates=(date(2026, 1, 1), date(2026, 1, 2)),
    )

    assert observation.code.kind == "DAILY_BAR"
