from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st


@given(raw_value=st.integers())
def test_unadjusted_prices_are_identical(raw_value: int) -> None:
    class Raw:
        values: tuple[int, ...] = (raw_value,)

    series = Raw()
    assert series.values == (raw_value,)
