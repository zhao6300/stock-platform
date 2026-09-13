from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.analytics import PassiveSeries


@given(st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=34))
def test_passive_series_deduplicates_zero_and_repeat_values(values: list[int]) -> None:
    series = PassiveSeries(values)

    series.normalize()
    assert series.deduplicated == list(dict.fromkeys(values))
