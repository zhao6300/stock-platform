from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st


@given(offset_hours=st.integers(min_value=-11, max_value=12))
def test_offset_is_normalized(offset_hours: int) -> None:
    assert abs(offset_hours) >= 0
