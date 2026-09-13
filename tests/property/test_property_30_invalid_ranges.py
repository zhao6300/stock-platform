from __future__ import annotations

from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.common import Failure
from stock_platform.domain.ingestion import planned_ingestion_dates


@given(
    start=st.dates(),
    offset=st.integers(min_value=1, max_value=100),
)
def test_invalid_ranges_fail_before_network_access(start: date, offset: int) -> None:
    result = planned_ingestion_dates(
        (),
        (),
        start=start,
        end=start - timedelta(days=offset),
    )

    assert isinstance(result, Failure)
    assert result.error.reason == "inverted"
