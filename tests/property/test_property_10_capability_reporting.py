from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from stock_platform.providers.capabilities import CapabilityValue


@given(
    reported=st.booleans(),
    rational_value=st.one_of(
        st.none(),
        st.text(),
        st.lists(st.text(), max_size=3),
    ),
)
def test_capability_values_preserve_known_and_unknown_semantics(
    reported: bool, rational_value: object | None
) -> None:
    capability = CapabilityValue(
        "provider-capability", rational_value, reported
    )

    if reported:
        assert capability.reported is True
        assert capability.rational_value == rational_value
    else:
        assert capability.reported is False
