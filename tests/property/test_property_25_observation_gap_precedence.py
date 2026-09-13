from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.calendars import (
    ObservationGapClassification,
    classify_observation_gap,
)


@given(
    trading_calendar_open=st.booleans(),
    tradability_status=st.one_of(
        st.sampled_from(("OPEN", "SUSPENDED", "UNKNOWN", "OTHER")),
        st.none(),
    ),
    valuation_expected=st.booleans(),
)
def test_observation_gap_reasons_follow_exact_precedence(
    trading_calendar_open: bool,
    tradability_status: str | None,
    valuation_expected: bool,
) -> None:
    result = classify_observation_gap(
        trading_calendar_open,
        tradability_status,
        valuation_expected,
    )

    if not trading_calendar_open:
        expected = ObservationGapClassification.EXPECTED_CALENDAR_GAP
    elif tradability_status == "SUSPENDED":
        expected = ObservationGapClassification.SUSPENDED_TRADING_GAP
    elif tradability_status is None or tradability_status == "UNKNOWN":
        expected = ObservationGapClassification.UNRESOLVED_GAP
    elif valuation_expected:
        expected = ObservationGapClassification.DELAYED_OR_MISSING_VALUATION
    else:
        expected = ObservationGapClassification.UNRESOLVED_GAP

    assert result == expected
