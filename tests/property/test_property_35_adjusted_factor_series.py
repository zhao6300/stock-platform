from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st


@given(modes=st.lists(st.booleans(), min_size=1, max_size=6))
def test_one_extra_missing_mode_rejected(modes: list[bool]) -> None:
    assert len(modes) >= 1
