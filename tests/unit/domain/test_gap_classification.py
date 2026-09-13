from __future__ import annotations

from datetime import UTC, date, datetime

from stock_platform.domain.calendars import ObservationGapReason, observation_gap_reason
from stock_platform.domain.observation import Observation, ObservationCode


def test_observation_gap_reason_is_exhaustive_for_each_context() -> None:
    security_id = "SEC-1"
    observation_date = date(2026, 1, 2)
    observation = Observation(
        code=ObservationCode(code="DAILY_BAR", kind="TRADING"),
        provider=security_id,
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        dates=(observation_date,),
    )

    assert (
        observation_gap_reason(security_id, observation_date, observation)
        == ObservationGapReason.MISSING_OR_UNKNOWN_TRADABILITY
    )


def test_observation_gap_reason_classifies_a_missing_security_master() -> None:
    security_id = "SEC-1"
    observation_date = date(2026, 1, 2)
    observation = Observation(
        code=ObservationCode(code="DAILY_BAR", kind="TRADING"),
        provider=security_id,
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        dates=(observation_date,),
    )

    assert (
        observation_gap_reason("", observation_date, observation)
        == ObservationGapReason.MISSING_SECURITY_MASTER
    )
