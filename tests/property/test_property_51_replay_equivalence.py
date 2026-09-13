from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.domain.research import replay_differences


@given(
    original=st.decimals(
        min_value=Decimal("1e-6"), max_value=Decimal("1e6"), allow_nan=False
    ),
    relative=st.floats(min_value=0, max_value=1e-13, allow_nan=False).map(Decimal),
)
def test_replay_equivalence_uses_exact_relative_tolerance(
    original: Decimal,
    relative: Decimal,
) -> None:
    replayed = original * (Decimal(1) + relative)
    assert replay_differences({"value": original}, {"value": replayed}) == ()
