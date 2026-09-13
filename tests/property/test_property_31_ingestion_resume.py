from __future__ import annotations

from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import Result, Success
from stock_platform.domain.ingestion import IngestionPlan, planned_ingestion_dates


@given(
    start=st.dates(),
    span=st.integers(min_value=0, max_value=10),
    finalized_count=st.integers(min_value=0, max_value=11),
)
def test_resume_planning_is_the_finalized_date_complement(
    start: date,
    span: int,
    finalized_count: int,
) -> None:
    expected = [start + timedelta(days=offset) for offset in range(span + 1)]
    finalized = expected[:finalized_count]
    end = expected[-1]

    result: Result[IngestionPlan, object] = planned_ingestion_dates(
        expected,
        finalized,
        start=start,
        end=end,
    )
    assert isinstance(result, Success)
    assert result.value.version_id
    assert result.value.requested_dates == tuple(d for d in expected if d not in finalized)
