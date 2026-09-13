from __future__ import annotations

from datetime import date

from hypothesis import assume, given
from hypothesis import strategies as st

from stock_platform.domain.common import Success
from stock_platform.domain.ingestion import planned_ingestion_dates


@given(
    expected_dates=st.lists(st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 1, 31))),
    existing_dates=st.lists(st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 1, 31))),
    start=st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 1, 31)),
    end=st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 1, 31)),
)
def test_non_refresh_planning_expands_to_maximal_missing_segments(
    expected_dates: list[date],
    existing_dates: list[date],
    start: date,
    end: date,
) -> None:
    assume(start <= end)
    result = planned_ingestion_dates(
        expected_dates,
        existing_dates,
        start=start,
        end=end,
        refresh=False,
    )

    assert isinstance(result, Success)
    requested = result.value.requested_dates
    applicable_expected = {item for item in expected_dates if start <= item <= end}
    applicable_existing = set(existing_dates) & applicable_expected
    assert set(requested) == applicable_expected - applicable_existing
